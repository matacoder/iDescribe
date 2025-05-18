# Voice Memos Transcription Agent

An automated Python agent that transcribes Voice Memos from iCloud on macOS.

## Features

- Automatically detects new .m4a files from Voice Memos
- Performs speech recognition with automatic language detection
- Saves transcriptions as .txt files in iCloud Drive/Transcribes
- Prevents duplicate processing
- Supports processing of the most recent recording

## Installation

1. Install Python 3 if not already installed
2. Install required package:
   ```bash
   pip install faster-whisper
   ```

## Setup

1. Copy the Python script to your desired location:
   ```bash
   cp watch_voicememos_faster.py ~/scripts/
   ```

2. Make sure you have full disk access for Python in System Settings > Privacy & Security > Full Disk Access

## Usage

To process the most recent Voice Memo:
```bash
python3 watch_voicememos_faster.py
```

The script will:
1. Find the most recent .m4a file in your Voice Memos
2. Transcribe it if it hasn't been processed before
3. Save the transcription to iCloud Drive/Transcribes

### Output Format

The transcription will be saved as a .txt file with:
- Language detection
- Duration of the recording
- Timestamps for each segment
- Full text transcription

Example output:
```
# Language: en | Duration: 30.5 sec

[0.0 – 5.2] First segment of speech
[5.2 – 12.8] Second segment of speech
...
```

## Requirements

- macOS
- Python 3
- iCloud enabled
- Full disk access for Python
- Voice Memos app with at least one recording

## Troubleshooting

If you get permission errors:
1. Make sure Python has full disk access in System Settings
2. Check that iCloud Drive is enabled and accessible
3. Verify that you have at least one Voice Memo recording 