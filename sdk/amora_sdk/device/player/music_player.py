"""
Music Player module for AmoraSDK Device.

Handles audio playback using MPD with Pipewire backend.
"""

import logging
import os
import time
import json
import subprocess
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

        try:
            # Ensure volume is within valid range
            volume = max(0, min(100, volume))
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
            volume = int(status.get("volume", "0"))
            return volume
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return 0

    def get_status(self) -> Dict[str, Any]:
        """
        Get player status.

        Returns:
            Dict[str, Any]: Player status
        """
        if not self._ensure_connected():
            return {"state": "disconnected"}

        try:
            status = self.mpd_client.status()
            current_song = None

            if status.get("state") != "stop":
                try:
                    song_info = self.mpd_client.currentsong()
                    if song_info:
                        # Extract file path and convert to relative path
                        file_path = song_info.get("file", "")

                        # Calculate position and duration in seconds
                        position = 0
                        if "time" in status and "elapsed" in status:
                            position = float(status.get("elapsed", "0"))

                        duration = 0
                        if "duration" in status:
                            duration = float(status.get("duration", "0"))
                        elif "time" in status:
                            time_parts = status.get("time", "0:0").split(":")
                            if len(time_parts) > 1:
                                duration = int(time_parts[1])

                        current_song = {
                            "title": song_info.get("title", os.path.basename(file_path)),
                            "artist": song_info.get("artist", "Unknown"),
                            "album": song_info.get("album", "Unknown"),
                            "file": file_path,
                            "duration": duration,
                            "position": position
                        }
                except Exception as e:
                    logger.error(f"Error getting current song info: {e}")

            # Get playlist name
            playlist = self.current_playlist

            # Build the status response
            result = {
                "state": status.get("state", "unknown"),
                "volume": int(status.get("volume", "0")),
                "current_song": current_song,
                "playlist": playlist,
                "repeat": status.get("repeat", "0") == "1",
                "random": status.get("random", "0") == "1"
            }

            return result
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {
                "state": "error",
                "error": str(e)
            }

    def get_playlists(self) -> List[str]:
        """
        Get available playlists.

        Returns:
            List[str]: List of playlist names
        """
        if not self._ensure_connected():
            return []

        try:
            playlists = self.mpd_client.listplaylists()
            return [playlist["playlist"] for playlist in playlists]
        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []

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
            logger.info("Database update started")
            return True
        except Exception as e:
            logger.error(f"Failed to update database: {e}")
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

        try:
            # Clear current playlist
            self.mpd_client.clear()

            # Load the playlist
            self.mpd_client.load(playlist_name)

            # Start playback
            self.mpd_client.play()

            # Store the current playlist name
            self.current_playlist = playlist_name

            logger.info(f"Playing playlist: {playlist_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to play playlist {playlist_name}: {e}")
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
            logger.info(f"Repeat mode set to {repeat}")
            return True
        except Exception as e:
            logger.error(f"Failed to set repeat mode: {e}")
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
            logger.info(f"Random mode set to {random}")
            return True
        except Exception as e:
            logger.error(f"Failed to set random mode: {e}")
            return False

    def create_playlist(self, playlist_name: str, files: List[str]) -> bool:
        """
        Create a new playlist.

        Args:
            playlist_name (str): Name of the playlist
            files (List[str]): List of music files to add to the playlist

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            # Create a new playlist
            self.mpd_client.clear()

            # Add files to the playlist
            for file in files:
                self.mpd_client.add(file)

            # Save the playlist
            self.mpd_client.save(playlist_name)

            logger.info(f"Created playlist: {playlist_name} with {len(files)} tracks")
            return True
        except Exception as e:
            logger.error(f"Failed to create playlist {playlist_name}: {e}")
            return False

    def delete_playlist(self, playlist_name: str) -> bool:
        """
        Delete a playlist.

        Args:
            playlist_name (str): Name of the playlist

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.mpd_client.rm(playlist_name)
            logger.info(f"Deleted playlist: {playlist_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete playlist {playlist_name}: {e}")
            return False

    def get_playlist_songs(self, playlist_name: str) -> List[Dict[str, Any]]:
        """
        Get the songs in a playlist.

        Args:
            playlist_name (str): Name of the playlist

        Returns:
            List[Dict[str, Any]]: List of songs in the playlist
        """
        if not self._ensure_connected():
            return []

        try:
            songs = self.mpd_client.listplaylistinfo(playlist_name)
            return songs
        except Exception as e:
            logger.error(f"Failed to get songs in playlist {playlist_name}: {e}")
            return []
