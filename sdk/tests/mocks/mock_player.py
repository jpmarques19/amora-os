"""
Mock player implementation for testing.
"""

from typing import Dict, Any, List, Optional

class MockMusicPlayer:
    """Mock music player for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the mock music player.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.connected = False
        self.current_playlist = None
        self.state = "stopped"
        self.volume = 50
        self.repeat = False
        self.random = False
        self.playlists = ["Test Playlist 1", "Test Playlist 2"]
        self.current_song = None
        
    def connect(self) -> bool:
        """
        Connect to the player.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.connected = True
        return True
        
    def disconnect(self) -> None:
        """Disconnect from the player."""
        self.connected = False
        
    def play(self) -> bool:
        """
        Start or resume playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.state = "playing"
        if not self.current_song:
            self.current_song = {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "file": "test.mp3",
                "duration": 180,
                "position": 0
            }
        return True
        
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.state == "playing":
            self.state = "paused"
        return True
        
    def stop(self) -> bool:
        """
        Stop playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.state = "stopped"
        self.current_song = None
        return True
        
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.current_song:
            self.current_song["title"] = "Next Song"
        return True
        
    def previous(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.current_song:
            self.current_song["title"] = "Previous Song"
        return True
        
    def set_volume(self, volume: int) -> bool:
        """
        Set volume level.
        
        Args:
            volume (int): Volume level (0-100)
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.volume = max(0, min(100, volume))
        return True
        
    def get_volume(self) -> int:
        """
        Get current volume level.
        
        Returns:
            int: Current volume level (0-100)
        """
        return self.volume
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get player status.
        
        Returns:
            Dict[str, Any]: Player status
        """
        return {
            "state": self.state,
            "volume": self.volume,
            "current_song": self.current_song,
            "playlist": self.current_playlist,
            "repeat": self.repeat,
            "random": self.random
        }
        
    def get_playlists(self) -> List[str]:
        """
        Get available playlists.
        
        Returns:
            List[str]: List of playlist names
        """
        return self.playlists
        
    def update_database(self) -> bool:
        """
        Update player database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return True
        
    def play_playlist(self, playlist_name: str) -> bool:
        """
        Play a playlist.
        
        Args:
            playlist_name (str): Name of the playlist
            
        Returns:
            bool: True if successful, False otherwise
        """
        if playlist_name in self.playlists:
            self.current_playlist = playlist_name
            self.state = "playing"
            self.current_song = {
                "title": f"{playlist_name} Song 1",
                "artist": "Test Artist",
                "album": "Test Album",
                "file": "test.mp3",
                "duration": 180,
                "position": 0
            }
            return True
        return False
        
    def set_repeat(self, repeat: bool) -> bool:
        """
        Set repeat mode.
        
        Args:
            repeat (bool): True to enable repeat, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.repeat = repeat
        return True
        
    def set_random(self, random: bool) -> bool:
        """
        Set random mode.
        
        Args:
            random (bool): True to enable random, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.random = random
        return True
