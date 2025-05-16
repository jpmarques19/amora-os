# Amora Music Player Application

This application integrates the Amora SDK player and broker modules using a procedural approach rather than an object-oriented one. It provides a complete music player solution that can be controlled via MQTT.

## Architecture

The application follows a procedural architecture with the following components:

1. **Player Module**: Imported from the Amora SDK, handles music playback and playlist management.
2. **Broker Module**: Imported from the Amora SDK, handles MQTT communication.
3. **Main Application**: Integrates the player and broker modules, handling the communication between them.

## Features

- Real-time player status updates via MQTT
- Command handling for controlling playback
- Automatic reconnection to MQTT broker
- Graceful shutdown handling
- Configurable update intervals

## Configuration

The application can be configured using a configuration file or environment variables. The following configuration options are available:

- `status_updater.enabled`: Enable or disable status updates (default: `true`)
- `status_updater.update_interval`: General update interval in seconds (default: `1.0`)
- `status_updater.position_update_interval`: Position update interval in seconds (default: `1.0`)
- `status_updater.full_update_interval`: Full update interval in seconds (default: `5.0`)

## Usage

### Prerequisites

- Python 3.7 or higher
- MPD (Music Player Daemon) installed and running
- MQTT broker (e.g., Mosquitto) installed and running

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/jpmarques19/amora-os.git
   cd amora-os
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

```
python edge/music_player_app.py
```

### MQTT Topics

The application uses the following MQTT topics:

- `amora/devices/{device_id}/state`: Player state updates
- `amora/devices/{device_id}/commands`: Commands to control the player
- `amora/devices/{device_id}/responses`: Responses to commands
- `amora/devices/{device_id}/connection`: Connection status

### Commands

The following commands are supported:

- `play`: Start or resume playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Skip to the next track
- `previous`: Skip to the previous track
- `set_volume`: Set the volume level (params: `{"volume": 75}`)
- `get_volume`: Get the current volume level
- `get_status`: Get the current player status
- `get_playlists`: Get available playlists
- `play_playlist`: Play a specific playlist (params: `{"playlist": "My Playlist"}`)
- `set_repeat`: Set repeat mode (params: `{"repeat": true}`)
- `set_random`: Set random mode (params: `{"random": true}`)
- `create_playlist`: Create a new playlist (params: `{"name": "New Playlist", "files": ["path/to/song.mp3"]}`)
- `delete_playlist`: Delete a playlist (params: `{"playlist": "My Playlist"}`)
- `get_playlist_songs`: Get songs in a playlist (params: `{"playlist": "My Playlist"}`)
- `update_database`: Update the music database

## Development

### Project Structure

```
edge/
├── config/
│   ├── config.json
│   └── config.dev.json
├── music_player_app.py
└── README_MUSIC_PLAYER.md
```

### Adding New Commands

To add a new command:

1. Implement the command in the player module
2. Add the command to the `standard_commands` list in the `register_command_handlers` function

### Testing

To test the application:

1. Start the application
2. Use an MQTT client (e.g., MQTT Explorer) to send commands and receive status updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
