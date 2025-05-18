import time
from pathlib import Path
from faster_whisper import WhisperModel
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

MODEL_SIZE = "large-v3"
COMPUTE_TYPE = "float32"
PROCESSED_LOG = Path.home() / ".voicememos_faster_done.txt"
VOICE_MEMOS_DEFAULT_PATH = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

OUTPUT_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Transcribes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_output_path(file_path: Path) -> Path:
    return OUTPUT_DIR / (file_path.stem + ".txt")

def load_processed_log() -> set[str]:
    if not PROCESSED_LOG.exists():
        return set()
    with open(PROCESSED_LOG, "r") as log:
        return set(line.strip() for line in log if line.strip())

def append_to_log(file_path: Path):
    with open(PROCESSED_LOG, "a") as log:
        log.write(str(file_path) + "\n")

def transcribe_file(file_path: Path, model: WhisperModel):
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
        append_to_log(file_path)
    except IOError as e:
        print(f"❌ Error writing transcription for {file_path.name} to {output_path}: {e}")

def wait_for_file_complete(path: Path, stable_seconds: float = 5.0) -> bool:
    last_size = -1
    stable_time = None
    while True:
        try:
            size = path.stat().st_size
        except Exception:
            size = -1
        now = time.time()
        if size == last_size and size > 0:
            if stable_time is None:
                stable_time = now
            elif now - stable_time >= stable_seconds:
                return True
        else:
            stable_time = None
        last_size = size
        time.sleep(0.2)

class VoiceMemoHandler(FileSystemEventHandler):
    def __init__(self, model, processed_files):
        self.model = model
        self.processed_files = processed_files
        self.in_progress = set()

    def try_process(self, path: Path):
        key = str(path)
        if path.suffix.lower() != ".m4a":
            return
        if key in self.processed_files or key in self.in_progress:
            return
        self.in_progress.add(key)
        try:
            if not wait_for_file_complete(path):
                return
            transcribe_file(path, self.model)
            self.processed_files.add(key)
        except Exception as e:
            print(f"❌ Error during transcription of {path.name}: {e}")
        finally:
            self.in_progress.discard(key)

    def on_created(self, event):
        if event.is_directory:
            return
        self.try_process(Path(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        self.try_process(Path(event.src_path))

def main():
    model = WhisperModel(MODEL_SIZE, compute_type=COMPUTE_TYPE)
    processed_files = load_processed_log()
    event_handler = VoiceMemoHandler(model, processed_files)
    observer = Observer()
    observer.schedule(event_handler, str(VOICE_MEMOS_DEFAULT_PATH), recursive=False)
    observer.start()
    print(f"👀 Watching {VOICE_MEMOS_DEFAULT_PATH} for new voice memos...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main() 