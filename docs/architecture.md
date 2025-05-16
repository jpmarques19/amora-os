# Amora SDK Architecture

This document describes the architecture of the Amora SDK, focusing on the separation of concerns between the player and broker modules.

## Overview

The Amora SDK is designed with a clean separation of concerns, ensuring that each module has a single responsibility and is decoupled from other modules. This architecture provides several benefits:

- **Loose coupling**: Modules can be developed, tested, and maintained independently.
- **Better testability**: Each module can be tested in isolation with mock dependencies.
- **Clearer responsibilities**: Each module has a well-defined purpose and API.
- **Flexibility**: Modules can be replaced or extended without affecting other parts of the system.

## Architecture Diagram

```
+------------------+       +------------------+       +------------------+
|                  |       |                  |       |                  |
|  Player Module   |<----->|  Application     |<----->|  Broker Module   |
|                  |       |  Layer           |       |                  |
+------------------+       +------------------+       +------------------+
```

## Modules

### Player Module

The player module is responsible for controlling music playback and retrieving player status. It has no knowledge of the broker module or how status updates are communicated to clients.

**Responsibilities**:
- Control music playback (play, pause, stop, etc.)
- Manage playlists
- Retrieve player status (current track, position, etc.)
- Handle audio output configuration

**API**:
- `connect()`: Connect to the music player daemon
- `disconnect()`: Disconnect from the music player daemon
- `get_status()`: Get the current player status
- `play()`: Start or resume playback
- `pause()`: Pause playback
- `stop()`: Stop playback
- `next()`: Skip to the next track
- `previous()`: Skip to the previous track
- `set_volume()`: Set the volume level
- `get_volume()`: Get the current volume level
- `get_playlists()`: Get available playlists
- `play_playlist()`: Play a specific playlist
- `get_playlist_songs()`: Get songs in a playlist
- `create_playlist()`: Create a new playlist
- `delete_playlist()`: Delete a playlist
- `set_repeat()`: Set repeat mode
- `set_random()`: Set random mode
- `update_database()`: Update the music database

### Broker Module

The broker module is responsible for MQTT communication with clients. It has no knowledge of the player module or how commands are executed.

**Responsibilities**:
- Connect to the MQTT broker
- Subscribe to command topics
- Publish status updates
- Handle command messages
- Manage connection status

**API**:
- `connect()`: Connect to the MQTT broker
- `disconnect()`: Disconnect from the MQTT broker
- `publish_state()`: Publish a state update
- `publish_response()`: Publish a command response
- `register_command_handler()`: Register a handler for a specific command
- `register_command_callback()`: Register a callback for all commands
- `register_state_change_callback()`: Register a callback for state changes

### Application Layer

The application layer integrates the player and broker modules, handling the communication between them. It receives commands from the broker module and forwards them to the player module, and retrieves status updates from the player module and forwards them to the broker module.

**Responsibilities**:
- Initialize and configure the player and broker modules
- Handle commands from the broker module and forward them to the player module
- Retrieve status updates from the player module and forward them to the broker module
- Manage status update frequency and optimization

**API**:
- `connect()`: Connect to services
- `disconnect()`: Disconnect from services
- `start_status_updates()`: Start automatic status updates
- `stop_status_updates()`: Stop automatic status updates

## Communication Flow

### Command Flow

1. The broker module receives a command message from a client via MQTT.
2. The broker module calls the registered command callback in the application layer.
3. The application layer calls the appropriate method on the player module.
4. The player module executes the command and returns the result.
5. The application layer creates a response message and forwards it to the broker module.
6. The broker module publishes the response message to the client via MQTT.

### Status Update Flow

1. The application layer periodically checks the player status.
2. The application layer retrieves the current status from the player module.
3. The application layer determines if an update should be sent based on changes and timing.
4. If an update is needed, the application layer forwards the status to the broker module.
5. The broker module publishes the status update to clients via MQTT.

## Example Usage

```python
from amora_sdk.device.player import MusicPlayer
from amora_sdk.device.broker.config import BrokerConfig
from amora_sdk.device.app import AmoraApp

# Create player
player_config = {...}
player = MusicPlayer(player_config)
player.connect()

# Create broker config
broker_config = BrokerConfig(...)

# Create app config
app_config = {...}

# Create app
app = AmoraApp(player, broker_config, app_config)

# Connect to services
app.connect()

# Application is now running
# Commands from clients will be forwarded to the player
# Status updates from the player will be forwarded to clients

# When done
app.disconnect()
player.disconnect()
```

## Testing

Each module can be tested independently with mock dependencies:

- **Player Module**: Test with a mock MPD client
- **Broker Module**: Test with a mock MQTT client
- **Application Layer**: Test with mock player and broker modules

This architecture ensures that tests are focused, reliable, and maintainable.
