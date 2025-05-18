#!/bin/bash

set -e

plist="$HOME/Library/LaunchAgents/com.idescribe.voicememos.plist"

if [ -f "$plist" ]; then
  echo "Unloading launch agent..."
  launchctl unload "$plist" || true
  rm "$plist"
  echo "Launch agent removed."
else
  echo "No launch agent found at $plist."
fi

echo "If you granted Full Disk Access to your Python interpreter, you may remove it in System Settings > Privacy & Security > Full Disk Access."
echo "You may also remove logs in /tmp/voicememos.out and /tmp/voicememos.err if desired." 