"""
Mock SDK modules for testing.

This module provides mock implementations of the SDK modules used by the MQTT Test Application.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
import time
import json
import uuid

# Mock QoS enum
class QoS(Enum):
    """MQTT Quality of Service levels."""
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2

# Mock TopicType enum
class TopicType(Enum):
    """Types of topics used in the Broker module."""
    STATE = "state"
    COMMANDS = "commands"
    RESPONSES = "responses"
    CONNECTION = "connection"

# Mock ConnectionOptions class
@dataclass
class ConnectionOptions:
    """MQTT connection options."""
    use_tls: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    keep_alive: int = 60
    clean_session: bool = True
    reconnect_on_failure: bool = True
    max_reconnect_delay: int = 300  # seconds

# Mock BrokerConfig class
@dataclass
class BrokerConfig:
    """Configuration for the Broker module."""
    broker_url: str
    port: int = 8883
    client_id: str = ""
    device_id: str = ""
    topic_prefix: str = "amora/devices"
    connection_options: ConnectionOptions = field(default_factory=ConnectionOptions)
    default_qos: QoS = QoS.AT_LEAST_ONCE

# Mock Message class
@dataclass
class Message:
    """Base class for MQTT messages."""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert the message to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a message from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

# Mock StateMessage class
@dataclass
class StateMessage(Message):
    """Message for device state updates."""
    state: str = ""
    current_song: Optional[Dict[str, Any]] = None
    volume: int = 0
    repeat: bool = False
    random: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "state": self.state,
            "current_song": self.current_song,
            "volume": self.volume,
            "repeat": self.repeat,
            "random": self.random
        }
    
    @classmethod
    def from_player_state(cls, player_state: Dict[str, Any]) -> 'StateMessage':
        """Create a StateMessage from player state."""
        return cls(
            state=player_state.get('state', ''),
            current_song=player_state.get('current_song'),
            volume=player_state.get('volume', 0),
            repeat=player_state.get('repeat', False),
            random=player_state.get('random', False)
        )

# Mock CommandMessage class
@dataclass
class CommandMessage(Message):
    """Message for device commands."""
    command: str = ""
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "command": self.command,
            "command_id": self.command_id,
            "params": self.params
        }

# Mock ResponseMessage class
@dataclass
class ResponseMessage(Message):
    """Message for command responses."""
    command_id: str = ""
    result: bool = False
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "command_id": self.command_id,
            "result": self.result,
            "message": self.message,
            "data": self.data
        }

# Mock ConnectionMessage class
@dataclass
class ConnectionMessage(Message):
    """Message for connection status."""
    status: str = "offline"  # "online" or "offline"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "status": self.status
        }

# Mock TopicManager class
class TopicManager:
    """Manages MQTT topics for the Broker module."""
    
    def __init__(self, topic_prefix: str, device_id: str):
        """Initialize the TopicManager."""
        self.topic_prefix = topic_prefix
        self.device_id = device_id
    
    def get_topic(self, topic_type: TopicType) -> str:
        """Get the full topic string for a given topic type."""
        return f"{self.topic_prefix}/{self.device_id}/{topic_type.value}"

# Mock MQTTClient class
class MQTTClient:
    """MQTT client wrapper for the Broker module."""
    
    def __init__(self, client_id: str, broker_url: str, port: int, options: ConnectionOptions):
        """Initialize the MQTT client."""
        self.client_id = client_id
        self.broker_url = broker_url
        self.port = port
        self.options = options
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.connected = False
    
    def publish(self, topic: str, payload: Union[str, Dict[str, Any], bytes],
                qos: QoS = QoS.AT_LEAST_ONCE, retain: bool = False) -> bool:
        """Publish a message to a topic."""
        return True
    
    def subscribe(self, topic: str, qos: QoS = QoS.AT_LEAST_ONCE,
                  callback: Optional[Callable[[str, bytes, Dict[str, Any]], None]] = None) -> bool:
        """Subscribe to a topic."""
        return True
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from a topic."""
        return True
    
    def set_last_will(self, topic: str, payload: Union[str, Dict[str, Any], bytes],
                      qos: QoS = QoS.AT_LEAST_ONCE, retain: bool = True) -> None:
        """Set the last will message."""
        pass
    
    def register_on_connect(self, callback: Callable[[bool], None]) -> None:
        """Register a callback for connection events."""
        pass
    
    def register_on_disconnect(self, callback: Callable[[], None]) -> None:
        """Register a callback for disconnection events."""
        pass

# Mock BrokerManager class
class BrokerManager:
    """Broker Manager for real-time communication using MQTT."""
    
    def __init__(self, config: BrokerConfig, player_interface=None):
        """Initialize the Broker Manager."""
        self.config = config
        self.player_interface = player_interface
        self.topic_manager = TopicManager(config.topic_prefix, config.device_id)
        self.mqtt_client = MQTTClient(
            client_id=config.client_id,
            broker_url=config.broker_url,
            port=config.port,
            options=config.connection_options
        )
        self.connected = False
        self.command_handlers = {}
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.connected = False
    
    def register_command_handler(self, command: str, handler: Callable) -> None:
        """Register a command handler."""
        self.command_handlers[command] = handler
    
    def publish_state(self, state: StateMessage) -> None:
        """Publish a state message."""
        pass
    
    def publish_response(self, response: ResponseMessage) -> None:
        """Publish a response message."""
        pass

# Mock MusicPlayer class
class MusicPlayer:
    """Music Player class for controlling MPD with Pipewire backend."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Music Player."""
        self.config = config
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to MPD server."""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from MPD server."""
        self.connected = False
    
    def play(self) -> bool:
        """Start or resume playback."""
        return True
    
    def pause(self) -> bool:
        """Pause playback."""
        return True
    
    def stop(self) -> bool:
        """Stop playback."""
        return True
    
    def next(self) -> bool:
        """Skip to next track."""
        return True
    
    def previous(self) -> bool:
        """Skip to previous track."""
        return True
    
    def set_volume(self, volume: int) -> bool:
        """Set volume level."""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get player status."""
        return {
            "state": "play",
            "volume": 50,
            "current_song": {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album"
            },
            "repeat": False,
            "random": False
        }
    
    def get_playlists(self) -> List[str]:
        """Get available playlists."""
        return ["playlist1", "playlist2", "playlist3"]
    
    def play_playlist(self, playlist_name: str) -> bool:
        """Play a playlist."""
        return True
