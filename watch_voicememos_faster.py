import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from faster_whisper import WhisperModel

MODEL_SIZE = "large-v3"
COMPUTE_TYPE = "float32"
PROCESSED_LOG = Path.home() / ".voicememos_faster_done.txt"

# === Find Voice Memos folder ===
def find_voicememo_folder():
    # Primary path for Voice Memos
    primary_path = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
    if primary_path.exists():
        files = list(primary_path.glob("*.m4a"))
        if files:
            return primary_path
    
    # Fallback paths
    fallback_paths = [
        Path.home() / "Library/Mobile Documents/com~apple~VoiceMemos/Documents",
        Path.home() / "Library/CloudStorage/iCloud Drive/Voice Memos",
        Path.home() / "Library/CloudStorage/iCloud Drive/Recordings",
        Path.home() / "Library/CloudStorage/iCloud Drive",
    ]
    
    for path in fallback_paths:
        if path.exists():
            files = list(path.glob("*.m4a"))
            if files:
                return path
                
    raise RuntimeError("❌ Voice Memos folder not found. Make sure iCloud is enabled and there's at least one recording.")

VOICE_MEMOS_DIR = find_voicememo_folder()
ICLOUD_ROOT = Path.home() / "Library/CloudStorage/iCloud Drive"

# === Setup output directory ===
def setup_output_directory():
    """Create and verify the output directory for transcriptions"""
    transcribes_dir = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Transcribes"
    try:
        # Create directory if it doesn't exist
        transcribes_dir.mkdir(parents=True, exist_ok=True)
        
        # Test if we can write to the directory
        test_file = transcribes_dir / ".test_write"
        test_file.touch()
        test_file.unlink()
        
        print(f"📁 Output directory ready: {transcribes_dir}")
        return transcribes_dir
    except Exception as e:
        raise RuntimeError(f"❌ Could not create or access output directory: {e}")

# === Determine output path for .txt file ===
def get_output_path(file_path: Path) -> Path:
    return OUTPUT_DIR / (file_path.stem + ".txt")

# === File processing ===
def get_recently_processed_files():
    """Get list of files processed in the last 24 hours"""
    if not PROCESSED_LOG.exists():
        return []
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    recent_files = []
    
    with open(PROCESSED_LOG, "r") as log:
        for line in log:
            file_path = Path(line.strip())
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > yesterday:
                    output_path = get_output_path(file_path)
                    if output_path.exists() and output_path.stat().st_size > 0:
                        recent_files.append((file_path, mtime))
    
    return sorted(recent_files, key=lambda x: x[1], reverse=True)

def is_already_processed(file_path):
    """Check if file is processed by verifying both log entry and transcription file"""
    # Check log entry
    if not PROCESSED_LOG.exists():
        return False
    
    with open(PROCESSED_LOG, "r") as log:
        if str(file_path) not in log.read():
            return False
    
    # Check if transcription file exists and is not empty
    output_path = get_output_path(file_path)
    if not output_path.exists():
        # Remove from log if file doesn't exist
        with open(PROCESSED_LOG, "r") as log:
            entries = [line for line in log if line.strip() != str(file_path)]
        with open(PROCESSED_LOG, "w") as log:
            log.writelines(entries)
        return False
    
    # Check if file is not empty
    if output_path.stat().st_size == 0:
        # Remove from log if file is empty
        with open(PROCESSED_LOG, "r") as log:
            entries = [line for line in log if line.strip() != str(file_path)]
        with open(PROCESSED_LOG, "w") as log:
            log.writelines(entries)
        output_path.unlink()  # Delete empty file
        return False
    
    return True

def mark_as_processed(file_path):
    with open(PROCESSED_LOG, "a") as log:
        log.write(str(file_path) + "\n")

def get_recent_recordings():
    """Find .m4a files from the last 24 hours"""
    files = list(VOICE_MEMOS_DIR.glob("*.m4a"))
    if not files:
        return []
    
    # Get current time and 24 hours ago
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    # Filter files from last 24 hours
    recent_files = [
        f for f in files 
        if datetime.fromtimestamp(f.stat().st_mtime) > yesterday
    ]
    
    return sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)

def transcribe_file(file_path: Path, model: WhisperModel):
    print(f"🎙 Transcribing: {file_path.name}")

    # Transcribe with progress, VAD initially disabled for diagnosis
    segments, info = model.transcribe(
        str(file_path),
        beam_size=5,
        language=None,  # Auto-detect language for each segment
        task="transcribe",
        vad_filter=False,  # Voice Activity Detection (disabled for now)
        # vad_parameters=dict(
        #     min_silence_duration_ms=500,  # Minimum silence duration to split segments
        #     speech_pad_ms=100,  # Padding around speech segments
        # )
    )
    duration = info.duration # Get duration from the single transcribe call

    output_text = f"# Duration: {duration:.1f} sec\n\n"
    current_time = 0

    for segment in segments:
        # Calculate and show progress
        progress = (segment.end / duration) * 100 if duration > 0 else 0
        print(f"\r⏳ Progress: {progress:.1f}% ({segment.end:.1f}/{duration:.1f}s)", end="", flush=True)

        output_text += f"[{segment.start:.1f} – {segment.end:.1f}] {segment.text.strip()}\n"
        current_time = segment.end

    print("\r✅ Transcription complete!      ")  # Extra spaces to clear the progress line

    output_path = get_output_path(file_path)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"📝 Saved to: {output_path}")
    mark_as_processed(file_path)

# === Test run ===
def main():
    global OUTPUT_DIR
    
    # Setup output directory first
    try:
        OUTPUT_DIR = setup_output_directory()
    except Exception as e:
        print(f"❌ {e}")
        return
    
    # Show recently processed files
    recent_processed = get_recently_processed_files()
    if recent_processed:
        print("\n📋 Recently processed files:")
        for file_path, mtime in recent_processed:
            print(f"   • {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        print()
    
    print(f"🚀 Looking for recordings from the last 24 hours in: {VOICE_MEMOS_DIR}")
    recent_files = get_recent_recordings()
    
    if not recent_files:
        print("❌ No recent recordings found in the last 24 hours")
        return
    
    print(f"📝 Found {len(recent_files)} recent recording(s)")
    
    # Load model only if we have files to transcribe
    print("📥 Loading model...")
    model = WhisperModel(MODEL_SIZE, compute_type=COMPUTE_TYPE)
    
    for file_path in recent_files:
        if not is_already_processed(file_path):
            print(f"\n📅 Processing: {file_path.name}")
            print(f"   Created: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                transcribe_file(file_path, model)
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                # Remove from log if processing failed
                with open(PROCESSED_LOG, "r") as log:
                    entries = [line for line in log if line.strip() != str(file_path)]
                with open(PROCESSED_LOG, "w") as log:
                    log.writelines(entries)
        else:
            print(f"ℹ️ Already processed: {file_path.name}")

if __name__ == "__main__":
    main() 