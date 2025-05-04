#!/usr/bin/env python3
"""
Music Player module for the Python Waybox application.
Handles audio playback using MPD with Pipewire backend.
"""

import logging
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from mpd import MPDClient

logger = logging.getLogger(__name__)

class MusicPlayer:
    """Music Player class for controlling MPD with Pipewire backend."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Music Player.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.mpd_client = MPDClient()
        self.mpd_host = config.get("mpd", {}).get("host", "localhost")
        self.mpd_port = config.get("mpd", {}).get("port", 6600)
        self.music_dir = config.get("content", {}).get("storage_path", "/home/user/music")
        self.playlists_dir = config.get("content", {}).get("playlists_path", "/home/user/music/playlists")
        self.connected = False
        self.current_playlist = None
        self.dev_mode = config.get("dev_mode", False)
    
    def connect(self) -> bool:
        """
        Connect to MPD server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.mpd_client.connect(self.mpd_host, self.mpd_port)
            self.connected = True
            logger.info("Connected to MPD server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MPD server: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MPD server."""
        if self.connected:
            try:
                self.mpd_client.close()
                self.mpd_client.disconnect()
                logger.info("Disconnected from MPD server")
            except Exception as e:
                logger.error(f"Error disconnecting from MPD server: {e}")
            finally:
                self.connected = False
    
    def _ensure_connected(self) -> bool:
        """
        Ensure connection to MPD server.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected:
            return self.connect()
        
        try:
            # Test connection with a simple command
            self.mpd_client.ping()
            return True
        except Exception:
            logger.warning("MPD connection lost, reconnecting...")
            return self.connect()
    
    def play(self) -> bool:
        """
        Start or resume playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.play()
            logger.info("Playback started")
            return True
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.pause(1)
            logger.info("Playback paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.stop()
            logger.info("Playback stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False
    
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.next()
            logger.info("Skipped to next track")
            return True
        except Exception as e:
            logger.error(f"Failed to skip to next track: {e}")
            return False
    
    def previous(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.previous()
            logger.info("Skipped to previous track")
            return True
        except Exception as e:
            logger.error(f"Failed to skip to previous track: {e}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """
        Set volume level.
        
        Args:
            volume (int): Volume level (0-100)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        # Ensure volume is within valid range
        volume = max(0, min(100, volume))
        
        try:
            self.mpd_client.setvol(volume)
            logger.info(f"Volume set to {volume}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    def get_volume(self) -> int:
        """
        Get current volume level.
        
        Returns:
            int: Current volume level (0-100)
        """
        if not self._ensure_connected():
            return 0
        
        try:
            status = self.mpd_client.status()
            return int(status.get("volume", 0))
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return 0
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get player status.
        
        Returns:
            Dict[str, Any]: Player status
        """
        status = {
            "state": "stopped",
            "volume": 0,
            "current_song": None,
            "playlist": self.current_playlist
        }
        
        if not self._ensure_connected():
            return status
        
        try:
            mpd_status = self.mpd_client.status()
            current_song = self.mpd_client.currentsong()
            
            status["state"] = mpd_status.get("state", "unknown")
            status["volume"] = int(mpd_status.get("volume", 0))
            
            if current_song:
                status["current_song"] = {
                    "title": current_song.get("title", "Unknown"),
                    "artist": current_song.get("artist", "Unknown"),
                    "album": current_song.get("album", "Unknown"),
                    "file": current_song.get("file", ""),
                    "duration": int(float(current_song.get("duration", 0))),
                    "position": int(float(mpd_status.get("elapsed", 0)))
                }
            
            return status
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return status
    
    def update_database(self) -> bool:
        """
        Update MPD database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.update()
            logger.info("MPD database update initiated")
            return True
        except Exception as e:
            logger.error(f"Failed to update MPD database: {e}")
            return False
    
    def get_playlists(self) -> List[str]:
        """
        Get available playlists.
        
        Returns:
            List[str]: List of playlist names
        """
        playlists = []
        
        # Check if playlists directory exists
        if not os.path.exists(self.playlists_dir):
            os.makedirs(self.playlists_dir, exist_ok=True)
            return playlists
        
        # Get subdirectories in playlists directory
        for item in os.listdir(self.playlists_dir):
            if os.path.isdir(os.path.join(self.playlists_dir, item)):
                playlists.append(item)
        
        return playlists
    
    def create_playlist(self, playlist_name: str, files: List[str] = None) -> bool:
        """
        Create a new playlist.
        
        Args:
            playlist_name (str): Name of the playlist
            files (List[str], optional): List of files to add to the playlist
        
        Returns:
            bool: True if successful, False otherwise
        """
        playlist_path = os.path.join(self.playlists_dir, playlist_name)
        
        try:
            # Create playlist directory if it doesn't exist
            if not os.path.exists(playlist_path):
                os.makedirs(playlist_path, exist_ok=True)
            
            # Create playlist metadata file
            metadata = {
                "name": playlist_name,
                "created": time.time(),
                "modified": time.time()
            }
            
            with open(os.path.join(playlist_path, "metadata.json"), "w") as f:
                json.dump(metadata, f)
            
            # Add files to playlist if provided
            if files:
                for file in files:
                    # TODO: Implement file copying or linking
                    pass
            
            logger.info(f"Created playlist: {playlist_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            return False
    
    def play_playlist(self, playlist_name: str) -> bool:
        """
        Play a playlist.
        
        Args:
            playlist_name (str): Name of the playlist
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        playlist_path = os.path.join(self.playlists_dir, playlist_name)
        
        if not os.path.exists(playlist_path):
            logger.error(f"Playlist not found: {playlist_name}")
            return False
        
        try:
            # Stop current playback and clear playlist
            self.mpd_client.stop()
            self.mpd_client.clear()
            
            # Add all files from the playlist directory
            for root, _, files in os.walk(playlist_path):
                for file in files:
                    if file.endswith((".mp3", ".flac", ".ogg", ".wav", ".wma")) and not file == "metadata.json":
                        relative_path = os.path.relpath(os.path.join(root, file), self.music_dir)
                        self.mpd_client.add(relative_path)
            
            # Start playback
            self.mpd_client.play()
            self.current_playlist = playlist_name
            
            logger.info(f"Playing playlist: {playlist_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to play playlist: {e}")
            return False
    
    def set_crossfade(self, seconds: int) -> bool:
        """
        Set crossfade between tracks.
        
        Args:
            seconds (int): Crossfade duration in seconds
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.crossfade(seconds)
            logger.info(f"Crossfade set to {seconds} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to set crossfade: {e}")
            return False
    
    def set_repeat(self, repeat: bool) -> bool:
        """
        Set repeat mode.
        
        Args:
            repeat (bool): True to enable repeat, False to disable
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.repeat(1 if repeat else 0)
            logger.info(f"Repeat {'enabled' if repeat else 'disabled'}")
            return True
        except Exception as e:
            logger.error(f"Failed to set repeat: {e}")
            return False
    
    def set_random(self, random: bool) -> bool:
        """
        Set random mode.
        
        Args:
            random (bool): True to enable random, False to disable
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            self.mpd_client.random(1 if random else 0)
            logger.info(f"Random {'enabled' if random else 'disabled'}")
            return True
        except Exception as e:
            logger.error(f"Failed to set random: {e}")
            return False
