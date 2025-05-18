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
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

1. Clone or copy this repository to a convenient folder (e.g., `~/dev/voice-memos-agent`).
2. Make sure the Python path in `com.user.voicememos.plist` matches your system (default: `/usr/bin/python3` or your venv path).
3. Install the launch agent for autostart:
   ```bash
   cp com.user.voicememos.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.user.voicememos.plist
   ```
   The script will now automatically start at login and run in the background.

4. Grant Python full disk access:
   - Open **System Settings → Privacy & Security → Full Disk Access**.
   - Click "+" and add the path to your Python interpreter (e.g., `/usr/bin/python3` or your venv path).
   - After adding, restart the script or your computer.

## Usage

The script will run in the background and automatically process new Voice Memos.

To run manually (for debugging):
```bash
python3 watch_voicememos_faster.py
```

### Output Format

The transcription will be saved as a .txt file with:
- Duration of the recording
- Timestamps for each segment
- Full text transcription

Example output:
```
# Duration: 30.5 sec

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
4. Check script logs: `/tmp/voicememos.out` and `/tmp/voicememos.err`
5. To restart the agent:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.voicememos.plist
   launchctl load ~/Library/LaunchAgents/com.user.voicememos.plist
   ``` 