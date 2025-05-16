"""
Mock objects for testing the MQTT Test Application.

This module provides mock objects for testing the MQTT Test Application
without requiring actual connections to MQTT brokers or MPD servers.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, Optional, List, Callable

class MockMusicPlayer:
    """Mock implementation of the MusicPlayer class."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the mock player."""
        self.config = config or {}
        self.connected = False
        self.current_playlist = None
        self.status = {
            "state": "stop",
            "volume": 50,
            "current_song": None,
            "repeat": False,
            "random": False
        }
        
        # Track method calls
        self.method_calls = []
    
    def connect(self) -> bool:
        """Mock connect method."""
        self.method_calls.append(("connect", []))
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Mock disconnect method."""
        self.method_calls.append(("disconnect", []))
        self.connected = False
    
    def play(self) -> bool:
        """Mock play method."""
        self.method_calls.append(("play", []))
        self.status["state"] = "play"
        return True
    
    def pause(self) -> bool:
        """Mock pause method."""
        self.method_calls.append(("pause", []))
        self.status["state"] = "pause"
        return True
    
    def stop(self) -> bool:
        """Mock stop method."""
        self.method_calls.append(("stop", []))
        self.status["state"] = "stop"
        return True
    
    def next(self) -> bool:
        """Mock next method."""
        self.method_calls.append(("next", []))
        return True
    
    def previous(self) -> bool:
        """Mock previous method."""
        self.method_calls.append(("previous", []))
        return True
    
    def set_volume(self, volume: int) -> bool:
        """Mock set_volume method."""
        self.method_calls.append(("set_volume", [volume]))
        self.status["volume"] = volume
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Mock get_status method."""
        self.method_calls.append(("get_status", []))
        return self.status
    
    def get_playlists(self) -> List[str]:
        """Mock get_playlists method."""
        self.method_calls.append(("get_playlists", []))
        return ["playlist1", "playlist2", "playlist3"]
    
    def play_playlist(self, playlist_name: str) -> bool:
        """Mock play_playlist method."""
        self.method_calls.append(("play_playlist", [playlist_name]))
        self.current_playlist = playlist_name
        self.status["state"] = "play"
        return True
    
    def set_repeat(self, repeat: bool) -> bool:
        """Mock set_repeat method."""
        self.method_calls.append(("set_repeat", [repeat]))
        self.status["repeat"] = repeat
        return True
    
    def set_random(self, random: bool) -> bool:
        """Mock set_random method."""
        self.method_calls.append(("set_random", [random]))
        self.status["random"] = random
        return True

class MockBrokerManager:
    """Mock implementation of the BrokerManager class."""
    
    def __init__(self, config=None, player_interface=None):
        """Initialize the mock broker manager."""
        self.config = config
        self.player_interface = player_interface
        self.connected = False
        self.command_handlers = {}
        self.state_change_callbacks = []
        self.response_callbacks = []
        self.published_messages = []
        self.mqtt_client = MagicMock()
        self.topic_manager = MagicMock()
        
        # Configure topic manager mock
        self.topic_manager.get_topic.return_value = "amora/test/amora-test-device/state"
    
    def connect(self) -> bool:
        """Mock connect method."""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Mock disconnect method."""
        self.connected = False
    
    def register_command_handler(self, command: str, handler: Callable) -> None:
        """Mock register_command_handler method."""
        self.command_handlers[command] = handler
    
    def register_state_change_callback(self, callback: Callable) -> None:
        """Mock register_state_change_callback method."""
        self.state_change_callbacks.append(callback)
    
    def register_response_callback(self, callback: Callable) -> None:
        """Mock register_response_callback method."""
        self.response_callbacks.append(callback)
    
    def publish_state(self, state) -> None:
        """Mock publish_state method."""
        self.published_messages.append(("state", state))
    
    def publish_response(self, response) -> None:
        """Mock publish_response method."""
        self.published_messages.append(("response", response))
    
    async def handle_command(self, command) -> None:
        """Mock handle_command method."""
        if command.command in self.command_handlers:
            response = await self.command_handlers[command.command](command)
            self.publish_response(response)

class AsyncMockBrokerManager(MockBrokerManager):
    """Async mock implementation of the BrokerManager class."""
    
    async def connect(self) -> bool:
        """Mock connect method."""
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """Mock disconnect method."""
        self.connected = False
