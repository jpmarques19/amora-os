"""
Message handling utilities for the Broker module.
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, Callable, Union, List
from dataclasses import dataclass, asdict, field


@dataclass
class Message:
    """Base class for MQTT messages."""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.

        Returns:
            Dictionary representation of the message
        """
        return asdict(self)

    def to_json(self) -> str:
        """
        Convert the message to a JSON string.

        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.

        Args:
            data: Dictionary representation of the message

        Returns:
            Message instance
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Create a message from a JSON string.

        Args:
            json_str: JSON string representation of the message

        Returns:
            Message instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class StateMessage(Message):
    """Message for device state updates."""
    state: str = ""
    current_song: Optional[Dict[str, Any]] = None
    volume: int = 0
    repeat: bool = False
    random: bool = False
    playlist: Optional[str] = None
    playlist_tracks: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_player_state(cls, player_state: Dict[str, Any]) -> 'StateMessage':
        """
        Create a StateMessage from player state.

        Args:
            player_state: Player state dictionary

        Returns:
            StateMessage instance
        """
        return cls(
            state=player_state.get('state', ''),
            current_song=player_state.get('current_song'),
            volume=player_state.get('volume', 0),
            repeat=player_state.get('repeat', False),
            random=player_state.get('random', False),
            playlist=player_state.get('playlist'),
            playlist_tracks=player_state.get('playlist_tracks')
        )


@dataclass
class CommandMessage(Message):
    """Message for device commands."""
    command: str = ""
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    params: Optional[Dict[str, Any]] = None


@dataclass
class ResponseMessage(Message):
    """Message for command responses."""
    command_id: str = ""
    result: bool = False
    message: str = ""
    data: Optional[Dict[str, Any]] = None


@dataclass
class ConnectionMessage(Message):
    """Message for connection status."""
    status: str = "offline"  # "online" or "offline"


def parse_message(payload: Union[str, bytes], message_type: Optional[str] = None) -> Optional[Message]:
    """
    Parse a message payload.

    Args:
        payload: Message payload
        message_type: Type of the message

    Returns:
        Parsed message or None if parsing failed
    """
    try:
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')

        data = json.loads(payload)

        if message_type == 'state':
            return StateMessage.from_dict(data)
        elif message_type == 'command':
            return CommandMessage.from_dict(data)
        elif message_type == 'response':
            return ResponseMessage.from_dict(data)
        elif message_type == 'connection':
            return ConnectionMessage.from_dict(data)
        else:
            # Try to determine the message type from the data
            if 'command' in data:
                return CommandMessage.from_dict(data)
            elif 'result' in data and 'command_id' in data:
                return ResponseMessage.from_dict(data)
            elif 'state' in data:
                return StateMessage.from_dict(data)
            elif 'status' in data:
                return ConnectionMessage.from_dict(data)
            else:
                return Message.from_dict(data)
    except Exception:
        return None
