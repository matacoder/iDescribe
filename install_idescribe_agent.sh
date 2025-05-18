#!/bin/bash

set -e

# Detect username and script path
your_username=$(whoami)
script_path=$(cd "$(dirname "$0")" && pwd)
plist_src="com.user.voicememos.plist"
plist_dst="$HOME/Library/LaunchAgents/com.idescribe.voicememos.plist"

# Prepare new plist with correct username and path
tmp_plist="/tmp/com.idescribe.voicememos.plist"
sed "s|<your_username>|$your_username|g; s|<your_path>|$(basename "$script_path")|g" "$plist_src" > "$tmp_plist"
sed -i '' "s|/Users/$your_username/$(basename "$script_path")|$script_path|g" "$tmp_plist"

# Copy to LaunchAgents
cp "$tmp_plist" "$plist_dst"

# Load agent
echo "Loading launch agent..."
launchctl unload "$plist_dst" 2>/dev/null || true
launchctl load "$plist_dst"

# Clean up
echo "Agent installed and loaded!"
echo "Check logs in /tmp/voicememos.out and /tmp/voicememos.err"
echo "Make sure to grant Full Disk Access to your Python interpreter in System Settings > Privacy & Security > Full Disk Access." 