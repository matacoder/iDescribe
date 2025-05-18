import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from faster_whisper import WhisperModel

MODEL_SIZE = "large-v3"
COMPUTE_TYPE = "float32"
PROCESSED_LOG = Path.home() / ".voicememos_faster_done.txt"

VOICE_MEMOS_DEFAULT_PATH = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

def initialize_voicememo_dir(path: Path) -> Path:
    if path.exists() and any(path.glob("*.m4a")):
        print(f"🎤 Voice Memos directory found: {path}")
        return path
    else:
        raise RuntimeError(
            f"❌ Voice Memos folder not found at {path} or it contains no .m4a files. "
            "Please ensure Voice Memos are stored in the default location and there's at least one recording."
        )

VOICE_MEMOS_DIR: Path = initialize_voicememo_dir(VOICE_MEMOS_DEFAULT_PATH)

def setup_output_directory() -> Path:
    transcribes_dir = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Transcribes"
    try:
        transcribes_dir.mkdir(parents=True, exist_ok=True)
        test_file = transcribes_dir / ".test_write"
        test_file.touch()
        test_file.unlink()
        print(f"📁 Output directory ready: {transcribes_dir}")
        return transcribes_dir
    except Exception as e:
        raise RuntimeError(f"❌ Could not create or access output directory {transcribes_dir}: {e}")

OUTPUT_DIR: Path = setup_output_directory()

def get_output_path(file_path: Path) -> Path:
    return OUTPUT_DIR / (file_path.stem + ".txt")

def get_recently_processed_files() -> list[tuple[Path, datetime]]:
    if not PROCESSED_LOG.exists():
        return []
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    recent_files: list[tuple[Path, datetime]] = []
    with open(PROCESSED_LOG, "r") as log:
        for line in log:
            file_path_str = line.strip()
            if not file_path_str:
                continue
            file_path = Path(file_path_str)
            if not file_path.exists():
                print(f" INFO: Logged recording {file_path.name} no longer exists. Consider removing from log if this is permanent.")
                continue
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > yesterday:
                    output_path = get_output_path(file_path)
                    if output_path.exists() and output_path.stat().st_size > 0:
                        recent_files.append((file_path, mtime))
            except FileNotFoundError:
                print(f" WARNING: File {file_path.name} from log not found during mtime check.")
                continue
    return sorted(recent_files, key=lambda x: x[1], reverse=True)

def is_already_processed(file_path: Path) -> bool:
    if not PROCESSED_LOG.exists():
        return False
    file_path_str = str(file_path)
    processed_entries: list[str] = []
    found_in_log = False
    with open(PROCESSED_LOG, "r") as log:
        processed_entries = log.readlines()
        if any(file_path_str == entry.strip() for entry in processed_entries):
            found_in_log = True
    if not found_in_log:
        return False
    output_path = get_output_path(file_path)
    needs_log_rewrite = False
    if not output_path.exists():
        print(f"🧹 Log entry for {file_path.name} exists, but output file {output_path.name} is missing. Removing from log.")
        needs_log_rewrite = True
    elif output_path.stat().st_size == 0:
        print(f"🧹 Log entry for {file_path.name} exists, but output file {output_path.name} is empty. Removing from log and deleting empty file.")
        try:
            output_path.unlink()
        except OSError as e:
            print(f" WARNING: Could not delete empty file {output_path}: {e}")
        needs_log_rewrite = True
    if needs_log_rewrite:
        updated_entries = [entry for entry in processed_entries if entry.strip() != file_path_str]
        with open(PROCESSED_LOG, "w") as log:
            log.writelines(updated_entries)
        return False
    return True

def mark_as_processed(file_path: Path) -> None:
    with open(PROCESSED_LOG, "a") as log:
        log.write(str(file_path) + "\n")

def get_recent_recordings() -> list[Path]:
    if not VOICE_MEMOS_DIR.exists():
        print(f" ERROR: Voice Memos directory {VOICE_MEMOS_DIR} not found.")
        return []
    files = list(VOICE_MEMOS_DIR.glob("*.m4a"))
    if not files:
        return []
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    recent_files = [
        f for f in files
        if datetime.fromtimestamp(f.stat().st_mtime) > yesterday
    ]
    return sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)

def transcribe_file(file_path: Path, model: WhisperModel) -> None:
    print(f"🎙 Transcribing: {file_path.name}")
    segments, info = model.transcribe(
        str(file_path),
        beam_size=10,
        language=None,
        task="transcribe",
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=100,
        )
    )
    duration = info.duration
    output_text = f"# Duration: {duration:.1f} sec\n\n"
    for segment in segments:
        progress = (segment.end / duration) * 100 if duration > 0 else 0
        print(f"\r⏳ Progress: {progress:.1f}% ({segment.end:.1f}/{duration:.1f}s)", end="", flush=True)
        output_text += f"[{segment.start:.1f} – {segment.end:.1f}] {segment.text.strip()}\n"
    print("\r✅ Transcription complete!      ")
    output_path = get_output_path(file_path)
    try:
        output_path.write_text(output_text, encoding="utf-8")
        print(f"📝 Saved to: {output_path}")
        mark_as_processed(file_path)
    except IOError as e:
        print(f"❌ Error writing transcription for {file_path.name} to {output_path}: {e}")

def main() -> None:
    recent_processed = get_recently_processed_files()
    if recent_processed:
        print("\n📋 Recently processed files (last 24h with valid transcriptions):")
        for file_path, mtime in recent_processed:
            print(f"   • {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        print()
    print(f"🚀 Looking for recordings from the last 24 hours in: {VOICE_MEMOS_DIR}")
    recent_files = get_recent_recordings()
    if not recent_files:
        print("🤷 No new recordings found in the last 24 hours.")
        return
    print(f"🎧 Found {len(recent_files)} recent recording(s) to check.")
    files_to_process = [f for f in recent_files if not is_already_processed(f)]
    if not files_to_process:
        print("✅ All recent recordings seem to be processed already.")
        return
    print(f"📥 Loading model {MODEL_SIZE} ({COMPUTE_TYPE})...")
    try:
        model = WhisperModel(MODEL_SIZE, compute_type=COMPUTE_TYPE)
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        print("   Ensure you have the necessary dependencies and model files accessible.")
        print("   Try running: pip install faster-whisper")
        return
    for file_path in files_to_process:
        print(f"\n📅 Processing: {file_path.name}")
        print(f"   Created: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            transcribe_file(file_path, model)
        except Exception as e:
            print(f"❌ Error during transcription of {file_path.name}: {e}")

if __name__ == "__main__":
    main() 