[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Voice Memos Transcription Agent

An automated Python agent that transcribes Voice Memos from iCloud on macOS.

## Features

- Automatically detects new .m4a files from Voice Memos
- Performs speech recognition with automatic language detection
- Saves transcriptions as .txt files in iCloud Drive/Transcribes
- Prevents duplicate processing
- Supports processing of the most recent recording

## Example Output

```
# Duration: 30.5 sec

[0.0 – 5.2] First segment of speech
[5.2 – 12.8] Second segment of speech
...
```

## Installation

1. Install Python 3 if not already installed
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Automatic Installation

To automatically set up the launch agent for background processing:

1. Run the install script from the project directory:
   ```bash
   bash install_idescribe_agent.sh
   ```
   This will:
   - Detect your username and the absolute path to the script
   - Generate a personalized launchd plist file
   - Copy it to `~/Library/LaunchAgents/com.idescribe.voicememos.plist`
   - Load the agent so it starts at login and runs in the background

2. Grant Python full disk access:
   - Open **System Settings → Privacy & Security → Full Disk Access**.
   - Click "+" and add the path to your Python interpreter (e.g., `/usr/bin/python3` or your venv path).
   - After adding, restart the script or your computer.

## Usage

The script will run in the background and automatically process new Voice Memos.

To run manually (for debugging):
```bash
python3 watch_voicememos_faster.py
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
   launchctl unload ~/Library/LaunchAgents/com.idescribe.voicememos.plist
   launchctl load ~/Library/LaunchAgents/com.idescribe.voicememos.plist
   ``` 