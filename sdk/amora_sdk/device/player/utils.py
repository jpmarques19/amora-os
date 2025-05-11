"""
Utility functions for the player module.
"""

import os
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def scan_music_directory(directory: str) -> List[str]:
    """
    Scan a directory for music files.
    
    Args:
        directory (str): Directory to scan
        
    Returns:
        List[str]: List of music files
    """
    music_extensions = [".mp3", ".flac", ".ogg", ".m4a", ".wav"]
    music_files = []
    
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in music_extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), directory)
                    music_files.append(rel_path)
    except Exception as e:
        logger.error(f"Error scanning music directory {directory}: {e}")
    
    return music_files

def create_playlist_file(playlist_name: str, files: List[str], playlists_dir: str) -> Optional[str]:
    """
    Create a playlist file.
    
    Args:
        playlist_name (str): Name of the playlist
        files (List[str]): List of music files
        playlists_dir (str): Directory to store playlists
        
    Returns:
        Optional[str]: Path to the playlist file, or None if creation failed
    """
    try:
        # Ensure the playlists directory exists
        os.makedirs(playlists_dir, exist_ok=True)
        
        # Create the playlist file
        playlist_path = os.path.join(playlists_dir, f"{playlist_name}.m3u")
        
        with open(playlist_path, "w") as f:
            f.write("#EXTM3U\n")
            for file in files:
                f.write(f"{file}\n")
        
        logger.info(f"Created playlist file: {playlist_path}")
        return playlist_path
    except Exception as e:
        logger.error(f"Error creating playlist file {playlist_name}: {e}")
        return None

def delete_playlist_file(playlist_name: str, playlists_dir: str) -> bool:
    """
    Delete a playlist file.
    
    Args:
        playlist_name (str): Name of the playlist
        playlists_dir (str): Directory containing playlists
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        playlist_path = os.path.join(playlists_dir, f"{playlist_name}.m3u")
        
        if os.path.exists(playlist_path):
            os.remove(playlist_path)
            logger.info(f"Deleted playlist file: {playlist_path}")
            return True
        else:
            logger.warning(f"Playlist file not found: {playlist_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting playlist file {playlist_name}: {e}")
        return False

def get_audio_devices() -> List[Dict[str, str]]:
    """
    Get available audio devices.
    
    Returns:
        List[Dict[str, str]]: List of audio devices
    """
    devices = []
    
    try:
        # Try to get audio devices using aplay
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            
            for line in lines:
                if line.startswith("card "):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        card_info = parts[0].strip()
                        device_name = parts[1].strip()
                        
                        # Extract card and device numbers
                        card_parts = card_info.split(" ")
                        if len(card_parts) >= 4:
                            card_num = card_parts[1]
                            device_num = card_parts[3]
                            
                            devices.append({
                                "card": card_num,
                                "device": device_num,
                                "name": device_name,
                                "id": f"hw:{card_num},{device_num}"
                            })
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
    
    return devices

def check_mpd_status() -> Tuple[bool, str]:
    """
    Check if MPD is running.
    
    Returns:
        Tuple[bool, str]: (is_running, status_message)
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "mpd"],
            capture_output=True,
            text=True,
            check=False
        )
        
        is_running = result.stdout.strip() == "active"
        status = "running" if is_running else "stopped"
        
        return is_running, status
    except Exception as e:
        logger.error(f"Error checking MPD status: {e}")
        return False, f"error: {str(e)}"

def start_mpd() -> bool:
    """
    Start MPD service.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["systemctl", "start", "mpd"],
            capture_output=True,
            text=True,
            check=False
        )
        
        success = result.returncode == 0
        if success:
            logger.info("MPD service started")
        else:
            logger.error(f"Failed to start MPD service: {result.stderr}")
        
        return success
    except Exception as e:
        logger.error(f"Error starting MPD service: {e}")
        return False

def stop_mpd() -> bool:
    """
    Stop MPD service.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["systemctl", "stop", "mpd"],
            capture_output=True,
            text=True,
            check=False
        )
        
        success = result.returncode == 0
        if success:
            logger.info("MPD service stopped")
        else:
            logger.error(f"Failed to stop MPD service: {result.stderr}")
        
        return success
    except Exception as e:
        logger.error(f"Error stopping MPD service: {e}")
        return False
