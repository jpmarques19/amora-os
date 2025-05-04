#!/usr/bin/env python3
"""
Test script for audio setup.
"""

import os
import sys
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import (
    run_command,
    get_audio_devices,
    get_pipewire_devices,
    get_iquadio_device,
    test_audio_device,
    is_pipewire_running,
    start_pipewire
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script."""
    logger.info("Testing audio setup...")
    
    # Check if Pipewire is running
    if is_pipewire_running():
        logger.info("Pipewire is running")
    else:
        logger.info("Pipewire is not running, starting...")
        if start_pipewire():
            logger.info("Pipewire started successfully")
        else:
            logger.error("Failed to start Pipewire")
    
    # List audio devices
    logger.info("Available audio devices:")
    devices = get_audio_devices()
    for device in devices:
        logger.info(device)
    
    # List Pipewire devices
    logger.info("Available Pipewire devices:")
    pw_devices = get_pipewire_devices()
    for device in pw_devices:
        logger.info(device)
    
    # Find IQUADIO DAC
    iquadio_device = get_iquadio_device()
    if iquadio_device:
        logger.info(f"Found IQUADIO DAC at {iquadio_device}")
        
        # Test IQUADIO DAC
        logger.info(f"Testing IQUADIO DAC...")
        if test_audio_device(iquadio_device):
            logger.info("IQUADIO DAC test successful!")
        else:
            logger.error("IQUADIO DAC test failed!")
    else:
        logger.error("IQUADIO DAC not found!")
    
    # Test MPD
    logger.info("Testing MPD...")
    stdout, stderr, return_code = run_command("mpc status")
    if return_code == 0:
        logger.info(f"MPD status: {stdout}")
    else:
        logger.error(f"MPD test failed: {stderr}")
    
    # Test playing a file with MPD
    logger.info("Testing MPD playback...")
    run_command("mpc clear")
    run_command("mpc volume 50")
    
    # Try to find a test file
    test_file = "/usr/share/sounds/alsa/Front_Center.wav"
    if os.path.exists(test_file):
        logger.info(f"Using test file: {test_file}")
        
        # Copy test file to music directory
        music_dir = os.path.expanduser("~/music")
        os.makedirs(music_dir, exist_ok=True)
        
        test_file_copy = os.path.join(music_dir, "test.wav")
        run_command(f"cp {test_file} {test_file_copy}")
        
        # Update MPD database
        run_command("mpc update")
        time.sleep(2)
        
        # Play test file
        run_command("mpc add test.wav")
        run_command("mpc play")
        
        logger.info("Playing test file for 5 seconds...")
        time.sleep(5)
        
        run_command("mpc stop")
        logger.info("Playback stopped")
    else:
        logger.error(f"Test file not found: {test_file}")
    
    logger.info("Audio test complete!")

if __name__ == "__main__":
    main()
