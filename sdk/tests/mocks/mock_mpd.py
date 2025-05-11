"""
Mock MPD client for testing.
"""

from typing import Dict, Any, List, Optional, Callable, Union


class MockMPDClient:
    """Mock MPD client for testing."""
    
    def __init__(self):
        """Initialize the mock MPD client."""
        self.connected = False
        self.timeout = 10
        self.status_data = {
            "state": "stop",
            "volume": "50",
            "repeat": "0",
            "random": "0",
            "single": "0",
            "consume": "0",
            "playlist": "0",
            "playlistlength": "0",
            "mixrampdb": "0.000000",
            "mixrampdelay": "nan"
        }
        self.current_song_data = {}
        self.playlists = []
        self.queue = []
        
    def connect(self, host: str, port: int) -> None:
        """
        Connect to MPD server.
        
        Args:
            host (str): MPD server host
            port (int): MPD server port
        """
        self.connected = True
        
    def disconnect(self) -> None:
        """Disconnect from MPD server."""
        self.connected = False
        
    def close(self) -> None:
        """Close the connection."""
        pass
        
    def ping(self) -> None:
        """Ping the server."""
        if not self.connected:
            raise ConnectionError("Not connected")
        
    def status(self) -> Dict[str, str]:
        """
        Get the current status.
        
        Returns:
            Dict[str, str]: Status data
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        return self.status_data
        
    def currentsong(self) -> Dict[str, str]:
        """
        Get the current song.
        
        Returns:
            Dict[str, str]: Current song data
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        return self.current_song_data
        
    def play(self, pos: int = 0) -> None:
        """
        Start playback.
        
        Args:
            pos (int, optional): Position to start playback from. Defaults to 0.
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["state"] = "play"
        
    def pause(self, pause: int = 1) -> None:
        """
        Pause playback.
        
        Args:
            pause (int, optional): 1 to pause, 0 to resume. Defaults to 1.
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["state"] = "pause" if pause == 1 else "play"
        
    def stop(self) -> None:
        """Stop playback."""
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["state"] = "stop"
        
    def next(self) -> None:
        """Skip to next track."""
        if not self.connected:
            raise ConnectionError("Not connected")
        
    def previous(self) -> None:
        """Skip to previous track."""
        if not self.connected:
            raise ConnectionError("Not connected")
        
    def setvol(self, volume: int) -> None:
        """
        Set volume.
        
        Args:
            volume (int): Volume level (0-100)
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["volume"] = str(volume)
        
    def repeat(self, state: int) -> None:
        """
        Set repeat mode.
        
        Args:
            state (int): 1 to enable, 0 to disable
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["repeat"] = str(state)
        
    def random(self, state: int) -> None:
        """
        Set random mode.
        
        Args:
            state (int): 1 to enable, 0 to disable
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.status_data["random"] = str(state)
        
    def update(self) -> None:
        """Update the music database."""
        if not self.connected:
            raise ConnectionError("Not connected")
        
    def listplaylists(self) -> List[Dict[str, str]]:
        """
        Get available playlists.
        
        Returns:
            List[Dict[str, str]]: List of playlists
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        return self.playlists
        
    def load(self, playlist_name: str) -> None:
        """
        Load a playlist.
        
        Args:
            playlist_name (str): Name of the playlist
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        
    def clear(self) -> None:
        """Clear the current playlist."""
        if not self.connected:
            raise ConnectionError("Not connected")
        self.queue = []
        
    def add(self, uri: str) -> None:
        """
        Add a song to the current playlist.
        
        Args:
            uri (str): URI of the song
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.queue.append(uri)
        
    def save(self, playlist_name: str) -> None:
        """
        Save the current playlist.
        
        Args:
            playlist_name (str): Name of the playlist
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.playlists.append({"playlist": playlist_name})
        
    def rm(self, playlist_name: str) -> None:
        """
        Delete a playlist.
        
        Args:
            playlist_name (str): Name of the playlist
        """
        if not self.connected:
            raise ConnectionError("Not connected")
        self.playlists = [p for p in self.playlists if p["playlist"] != playlist_name]
