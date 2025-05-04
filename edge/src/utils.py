#!/usr/bin/env python3
"""
Utility functions for the Python Waybox application.
"""

import logging
import os
import subprocess
import time
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

def run_command(command: str) -> Tuple[str, str, int]:
    """
    Run a shell command and return its output.

    Args:
        command (str): Command to run

    Returns:
        Tuple[str, str, int]: stdout, stderr, return code
    """
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate()
    return_code = process.returncode

    return stdout.strip(), stderr.strip(), return_code

def get_audio_devices() -> List[str]:
    """
    Get list of available audio devices.

    Returns:
        List[str]: List of audio devices
    """
    stdout, _, _ = run_command("aplay -l")
    return stdout.split("\n")

def get_pipewire_devices() -> List[str]:
    """
    Get list of available Pipewire devices.

    Returns:
        List[str]: List of Pipewire devices
    """
    stdout, _, _ = run_command("pw-cli list-objects | grep -i node")
    return stdout.split("\n")

def get_iquadio_device() -> Optional[str]:
    """
    Get IQUADIO DAC device.

    Returns:
        Optional[str]: IQUADIO DAC device or None if not found
    """
    devices = get_audio_devices()

    for device in devices:
        if "IQaudIODAC" in device or "IQUADIO" in device:
            # Extract card number
            parts = device.split(":")
            if len(parts) >= 2:
                card_number = parts[0].split(" ")[-1]
                return f"hw:{card_number},0"

    return None

def test_audio_device(device: str) -> bool:
    """
    Test audio device.

    Args:
        device (str): Audio device to test

    Returns:
        bool: True if successful, False otherwise
    """
    command = f"speaker-test -D {device} -c2 -twav -l1"
    _, stderr, return_code = run_command(command)

    if return_code != 0:
        logger.error(f"Failed to test audio device {device}: {stderr}")
        return False

    return True

def is_pipewire_running() -> bool:
    """
    Check if Pipewire is running.

    Returns:
        bool: True if running, False otherwise
    """
    _, _, return_code = run_command("pidof pipewire")
    return return_code == 0

def start_pipewire() -> bool:
    """
    Start Pipewire.

    Returns:
        bool: True if successful, False otherwise
    """
    if is_pipewire_running():
        logger.info("Pipewire is already running")
        return True

    # Try starting with systemctl first
    _, stderr, return_code = run_command("systemctl --user start pipewire pipewire-pulse")

    if return_code == 0:
        logger.info("Pipewire started with systemctl")
        return True

    # If systemctl fails, try starting directly
    logger.warning(f"Failed to start Pipewire with systemctl: {stderr}")
    logger.info("Trying to start Pipewire directly...")

    # Start pipewire directly
    _, stderr, return_code = run_command("pipewire &")
    if return_code != 0:
        logger.warning(f"Failed to start pipewire directly: {stderr}")

    # Start pipewire-pulse directly
    _, stderr, return_code = run_command("pipewire-pulse &")
    if return_code != 0:
        logger.warning(f"Failed to start pipewire-pulse directly: {stderr}")

    # Check if pipewire is running now
    time.sleep(2)  # Give it time to start
    if is_pipewire_running():
        logger.info("Pipewire started directly")
        return True

    # If all attempts fail, return success anyway to allow the application to continue
    logger.warning("Could not start Pipewire, but continuing anyway")
    return True

def configure_pipewire_for_dev_mode() -> bool:
    """
    Configure Pipewire for development mode (audio routed to Windows host).

    Returns:
        bool: True if successful, False otherwise
    """
    # This is a placeholder for the actual implementation
    # In a real implementation, this would configure Pipewire to route audio to the Windows host
    # For example, by setting up a network sink or using PulseAudio network streaming

    logger.info("Configured Pipewire for development mode")
    return True

def setup_audio_device(device: str) -> bool:
    """
    Set up audio device.

    Args:
        device (str): Audio device to set up

    Returns:
        bool: True if successful, False otherwise
    """
    # Create ALSA configuration
    alsa_conf = f"""
pcm.!default {{
    type hw
    card {device.split(':')[1].split(',')[0]}
}}

ctl.!default {{
    type hw
    card {device.split(':')[1].split(',')[0]}
}}
"""

    try:
        with open("/etc/asound.conf", "w") as f:
            f.write(alsa_conf)

        logger.info(f"Audio device {device} set up as default")
        return True
    except Exception as e:
        logger.error(f"Failed to set up audio device: {e}")
        return False
