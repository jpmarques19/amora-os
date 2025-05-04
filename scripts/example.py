#!/usr/bin/env python3
"""
Example script demonstrating how to use the MusicPlayer class.
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
    """Main entry point for the script."""
    logger.info("Starting example player script...")
    
    # Create configuration
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
    
    # Connect to MPD
    if not player.connect():
        logger.error("Failed to connect to MPD. Exiting.")
        return 1
    
    try:
        # Set initial volume
        player.set_volume(70)
        logger.info(f"Volume set to: {player.get_volume()}")
        
        # Create a test playlist if it doesn't exist
        playlists = player.get_playlists()
        logger.info(f"Available playlists: {playlists}")
        
        if "test_playlist" not in playlists:
            logger.info("Creating test playlist...")
            player.create_playlist("test_playlist")
        
        # Try to find a test file
        test_file = "/usr/share/sounds/alsa/Front_Center.wav"
        if os.path.exists(test_file):
            logger.info(f"Using test file: {test_file}")
            
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
            
            # Test play
            logger.info("Testing play...")
            player.play()
            time.sleep(2)
            
            # Test pause
            logger.info("Testing pause...")
            player.pause()
            time.sleep(2)
            
            # Test play (resume)
            logger.info("Testing resume...")
            player.play()
            time.sleep(2)
            
            # Test stop
            logger.info("Testing stop...")
            player.stop()
            time.sleep(2)
            
            # Get player status
            status = player.get_status()
            logger.info(f"Player status: {status}")
        else:
            logger.error(f"Test file not found: {test_file}")
        
        # Disconnect from MPD
        player.disconnect()
        
        logger.info("Example script completed")
        return 0
    
    except Exception as e:
        logger.exception(f"Error in example script: {e}")
        player.disconnect()
        return 1

if __name__ == "__main__":
    main()
