#!/usr/bin/env python3
"""
Simple example of using the MusicPlayer directly.
"""

import os
import sys
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from player import MusicPlayer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Simple example of using the MusicPlayer."""
    # Create a simple configuration
    config = {
        "mpd": {
            "host": "localhost",
            "port": 6600
        },
        "content": {
            "storage_path": "/home/user/music",
            "playlists_path": "/home/user/music/playlists"
        },
        "audio": {
            "backend": "pipewire",
            "device": "default",
            "volume": 80
        },
        "dev_mode": False
    }
    
    # Create player instance
    player = MusicPlayer(config)
    
    try:
        # Connect to MPD
        if not player.connect():
            logger.error("Failed to connect to MPD")
            return 1
        
        # Get player status
        status = player.get_status()
        logger.info(f"Player status: {status}")
        
        # Set volume
        player.set_volume(75)
        logger.info(f"Volume set to: {player.get_volume()}")
        
        # Play a test file if available
        test_file = "/usr/share/sounds/alsa/Front_Center.wav"
        if os.path.exists(test_file):
            # Copy test file to music directory
            music_dir = config["content"]["storage_path"]
            os.makedirs(music_dir, exist_ok=True)
            
            test_file_copy = os.path.join(music_dir, "test.wav")
            os.system(f"cp {test_file} {test_file_copy}")
            
            # Update MPD database
            player.update_database()
            time.sleep(2)
            
            # Play test file
            player.mpd_client.clear()
            player.mpd_client.add("test.wav")
            player.play()
            
            logger.info("Playing test file for 5 seconds...")
            time.sleep(5)
            
            player.stop()
            logger.info("Playback stopped")
        else:
            logger.warning(f"Test file not found: {test_file}")
        
        # Disconnect from MPD
        player.disconnect()
        return 0
    
    except Exception as e:
        logger.exception(f"Error: {e}")
        if player.connected:
            player.disconnect()
        return 1

if __name__ == "__main__":
    sys.exit(main())
