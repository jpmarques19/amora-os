# MQTT Test Application for AmoraSDK

This test application demonstrates how to use the AmoraSDK to control the music player via MQTT commands. It serves as a proof of concept for the real-time communication implementation in the AmoraOS project.

## Overview

The application consists of two components:

1. **Server Component**: Sets up the player, configures MQTT broker communication, handles incoming commands, and broadcasts player status updates.
2. **Client Component**: A CLI application that allows the user to send commands to the player and displays real-time player status updates.

## Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)
- MPD (Music Player Daemon) running on the server
- MQTT broker (e.g., Mosquitto, HiveMQ, etc.)

## Installation

1. Clone the repository and navigate to the SDK directory:

```bash
git clone https://github.com/jpmarques19/amora-os.git
cd amora-os/sdk
```

2. Install dependencies using Poetry:

```bash
poetry install
```

3. Create a credentials file:

```bash
poetry run python -m test_app.mqtt_test.run init --config credentials_configs.txt
```

4. Edit the credentials file with your MQTT broker and player configuration.

## Configuration

The application uses a JSON configuration file (`credentials_configs.txt`) with the following structure:

```json
{
    "mqtt": {
        "broker_url": "localhost",
        "port": 1883,
        "username": "your_username",
        "password": "your_password",
        "device_id": "amora-player-001",
        "topic_prefix": "amora/devices",
        "use_tls": false,
        "keep_alive": 60,
        "clean_session": true,
        "reconnect_on_failure": true,
        "max_reconnect_delay": 300,
        "default_qos": 1
    },
    "player": {
        "mpd_host": "localhost",
        "mpd_port": 6600,
        "storage_path": "/home/user/music",
        "playlists_path": "/home/user/music/playlists",
        "audio_backend": "pipewire",
        "audio_device": "default",
        "audio_volume": 80,
        "dev_mode": true
    }
}
```

You can also use environment variables to override the configuration:

- `MQTT_BROKER_URL`: MQTT broker URL
- `MQTT_PORT`: MQTT broker port
- `MQTT_USERNAME`: MQTT username
- `MQTT_PASSWORD`: MQTT password
- `MQTT_DEVICE_ID`: Device ID
- `MPD_HOST`: MPD host
- `MPD_PORT`: MPD port

## Usage

### Running the Server

The server component connects to the MPD server and MQTT broker, handles incoming commands, and broadcasts player status updates.

```bash
poetry run python -m test_app.mqtt_test.run server --config credentials_configs.txt
```

### Running the Client

The client component connects to the MQTT broker, sends commands to the server, and displays real-time player status updates.

```bash
poetry run python -m test_app.mqtt_test.run client --config credentials_configs.txt
```

### Client Commands

The client provides a command-line interface with the following commands:

- `play`: Start playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Skip to next track
- `prev` or `previous`: Skip to previous track
- `vol <level>` or `volume <level>`: Set volume (0-100)
- `status`: Get player status
- `playlists`: Get available playlists
- `playlist <name>`: Play a specific playlist
- `quit` or `exit`: Exit the application

## MQTT Communication

The application uses the following MQTT topics for communication:

- `amora/devices/<device_id>/commands`: Commands from client to server
- `amora/devices/<device_id>/responses`: Command responses from server to client
- `amora/devices/<device_id>/state`: Player state updates from server to client
- `amora/devices/<device_id>/connection`: Connection status updates

### Message Formats

#### Command Message

```json
{
    "command": "play",
    "command_id": "550e8400-e29b-41d4-a716-446655440000",
    "params": null,
    "timestamp": 1620000000.0
}
```

#### Response Message

```json
{
    "command_id": "550e8400-e29b-41d4-a716-446655440000",
    "result": true,
    "message": "Play command executed",
    "data": null,
    "timestamp": 1620000001.0
}
```

#### State Message

```json
{
    "state": "play",
    "current_song": {
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "file": "path/to/song.mp3",
        "duration": 180.0,
        "position": 45.5
    },
    "volume": 80,
    "repeat": false,
    "random": false,
    "timestamp": 1620000002.0
}
```

## Architecture

### Server Component

The server component uses the following classes from the AmoraSDK:

- `MusicPlayer`: Interfaces with MPD to control music playback
- `BrokerManager`: Manages MQTT communication
- `BrokerConfig`: Configures the MQTT broker connection
- `TopicManager`: Manages MQTT topics

The server registers command handlers for each supported command and periodically publishes player state updates.

### Client Component

The client component uses the following classes from the AmoraSDK:

- `BrokerManager`: Manages MQTT communication
- `BrokerConfig`: Configures the MQTT broker connection
- `TopicManager`: Manages MQTT topics

The client subscribes to state and response topics, sends commands to the server, and displays real-time player status updates using the curses library.

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Check that your MQTT broker is running and accessible
2. Verify that your credentials are correct
3. Check that the MPD server is running and accessible
4. Check the logs for error messages

### Logging

The application logs to the following files:

- Server: Standard output
- Client: `mqtt_client.log`

## Development

### Adding New Commands

To add a new command:

1. Add a command handler in the server component
2. Update the client component to send the new command
3. Update the README.md with the new command

### Testing

To test the application:

1. Run the server component
2. Run the client component
3. Send commands from the client and verify that they are executed by the server

## License

This project is licensed under the same license as the AmoraOS project.
