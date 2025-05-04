#!/bin/bash
# Simple script to play a sample music file using MPD/MPC
# This script is meant to be run inside the container

# Update MPD database
echo "Updating MPD database..."
mpc update
sleep 2

# List available music files
echo "Available music files:"
find /home/user/music -type f -name "*.mp3" | sort

# Clear current playlist
mpc clear

# Add all MP3 files to the playlist
echo "Adding music files to playlist..."
find /home/user/music -type f -name "*.mp3" -exec mpc add {} \;

# Show the playlist
echo "Current playlist:"
mpc playlist

# Start playback
echo "Starting playback..."
mpc play

# Show current status
echo "Current status:"
mpc status

echo "Use 'mpc next' to play the next track"
echo "Use 'mpc prev' to play the previous track"
echo "Use 'mpc stop' to stop playback"
echo "Use 'mpc pause' to pause playback"
echo "Use 'mpc volume 80' to set volume to 80%"
