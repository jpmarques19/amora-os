#!/bin/bash

# Create necessary directories
mkdir -p /home/user/music/playlists
mkdir -p /home/user/.config/mpd
mkdir -p /home/user/.local/share/mpd
mkdir -p /home/user/logs

# Copy MPD configuration
cp /home/user/app/config/mpd.conf /home/user/.config/mpd/mpd.conf

# Start Pipewire in the background
systemctl --user start pipewire pipewire-pulse
sleep 2

# Start MPD
mpd /home/user/.config/mpd/mpd.conf
sleep 2

# Set volume
amixer set Master 100%

# Start the Python application
cd /home/user/app
python3 src/main.py

# Keep container running if the application exits
tail -f /dev/null
