# MQTT Topics and Message Formats

This document describes the MQTT topics and message formats used by the Amora Client SDK for communication with Amora music player devices.

## Topic Structure

The Amora Client SDK uses a hierarchical topic structure to organize communication between clients and devices:

```
{topicPrefix}/{deviceId}/{topicType}
```

Where:
- `topicPrefix`: Base prefix for all Amora topics (default: `amora/devices`)
- `deviceId`: Unique identifier for the device
- `topicType`: Type of message being sent or received

## Topic Types

The SDK uses the following topic types:

| Topic Type | Direction | Description |
|------------|-----------|-------------|
| `state` | Device → Client | Player state updates |
| `commands` | Client → Device | Commands to the player |
| `responses` | Device → Client | Command responses from the player |
| `connection` | Device → Client | Connection status updates |

## Example Topics

For a device with ID `amora-player-001` and the default topic prefix:

- `amora/devices/amora-player-001/state`: Player state updates
- `amora/devices/amora-player-001/commands`: Commands to the player
- `amora/devices/amora-player-001/responses`: Command responses from the player
- `amora/devices/amora-player-001/connection`: Connection status updates

## Message Formats

All messages are JSON-encoded and include a timestamp field.

### State Messages

State messages are published by the device to the `state` topic to provide real-time updates about the player's status.

```json
{
  "state": "playing",
  "currentSong": {
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "albumArt": "http://example.com/album-art.jpg",
    "duration": 180,
    "file": "path/to/song.mp3"
  },
  "position": 45,
  "volume": 80,
  "repeat": false,
  "random": false,
  "timestamp": 1616161616161
}
```

| Field | Type | Description |
|-------|------|-------------|
| `state` | string | Current player state: `playing`, `paused`, `stopped`, `loading`, `error` |
| `currentSong` | object | Metadata for the current song (optional) |
| `position` | number | Current playback position in seconds (optional) |
| `volume` | number | Current volume level (0-100) |
| `repeat` | boolean | Whether repeat mode is enabled |
| `random` | boolean | Whether random mode is enabled |
| `timestamp` | number | Unix timestamp in milliseconds |

### Command Messages

Command messages are published by clients to the `commands` topic to control the player.

```json
{
  "command": "play",
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "params": {
    "trackId": "123"
  },
  "timestamp": 1616161616161
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Command name |
| `commandId` | string | Unique identifier for the command (UUID) |
| `params` | object | Command parameters (optional) |
| `timestamp` | number | Unix timestamp in milliseconds |

### Response Messages

Response messages are published by the device to the `responses` topic in response to commands.

```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "result": true,
  "message": "Command executed successfully",
  "data": {
    "state": "playing",
    "position": 0
  },
  "timestamp": 1616161616161
}
```

| Field | Type | Description |
|-------|------|-------------|
| `commandId` | string | ID of the command this response is for |
| `result` | boolean | Whether the command was successful |
| `message` | string | Human-readable message |
| `data` | object | Additional data (optional) |
| `timestamp` | number | Unix timestamp in milliseconds |

### Connection Messages

Connection messages are published by the device to the `connection` topic to indicate its connection status.

```json
{
  "status": "online",
  "timestamp": 1616161616161
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Connection status: `online` or `offline` |
| `timestamp` | number | Unix timestamp in milliseconds |

## Supported Commands

The SDK supports the following commands:

### Basic Playback Controls

| Command | Parameters | Description |
|---------|------------|-------------|
| `play` | None | Start playback |
| `pause` | None | Pause playback |
| `stop` | None | Stop playback |
| `next` | None | Skip to the next track |
| `previous` | None | Go back to the previous track |

### Volume Controls

| Command | Parameters | Description |
|---------|------------|-------------|
| `setVolume` | `{ "volume": number }` | Set the volume (0-100) |

### Playback Mode Controls

| Command | Parameters | Description |
|---------|------------|-------------|
| `setRepeat` | `{ "repeat": boolean }` | Set repeat mode |
| `setRandom` | `{ "random": boolean }` | Set random mode |

### Status and Information

| Command | Parameters | Description |
|---------|------------|-------------|
| `getStatus` | None | Get the current player status |
| `getPlaylists` | None | Get the available playlists |

### Playlist Management

| Command | Parameters | Description |
|---------|------------|-------------|
| `playPlaylist` | `{ "playlist": string }` | Play a playlist |
| `playTrack` | `{ "trackIndex": number }` | Play a specific track |
| `addTrack` | `{ "track": string, "playlist": string }` | Add a track to a playlist |
| `removeTrack` | `{ "trackIndex": number, "playlist": string }` | Remove a track from a playlist |
| `reorderTrack` | `{ "fromIndex": number, "toIndex": number, "playlist": string }` | Reorder tracks in a playlist |

## Command Response Data

Different commands return different data in their responses:

### getStatus Response

```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "result": true,
  "message": "Status retrieved",
  "data": {
    "state": "playing",
    "currentSong": {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "albumArt": "http://example.com/album-art.jpg",
      "duration": 180,
      "file": "path/to/song.mp3"
    },
    "position": 45,
    "volume": 80,
    "repeat": false,
    "random": false
  },
  "timestamp": 1616161616161
}
```

### getPlaylists Response

```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "result": true,
  "message": "Playlists retrieved",
  "data": {
    "playlists": [
      {
        "name": "Playlist 1",
        "items": [
          {
            "title": "Song 1",
            "artist": "Artist 1",
            "album": "Album 1",
            "albumArt": "http://example.com/album1.jpg",
            "duration": 180,
            "file": "path/to/song1.mp3",
            "position": 0,
            "isCurrent": true
          },
          {
            "title": "Song 2",
            "artist": "Artist 2",
            "album": "Album 2",
            "albumArt": "http://example.com/album2.jpg",
            "duration": 240,
            "file": "path/to/song2.mp3",
            "position": 1,
            "isCurrent": false
          }
        ]
      },
      {
        "name": "Playlist 2",
        "items": [
          {
            "title": "Song 3",
            "artist": "Artist 3",
            "album": "Album 3",
            "albumArt": "http://example.com/album3.jpg",
            "duration": 200,
            "file": "path/to/song3.mp3",
            "position": 0,
            "isCurrent": false
          }
        ]
      }
    ]
  },
  "timestamp": 1616161616161
}
```

## Error Handling

When a command fails, the response will have `result: false` and include an error message:

```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "result": false,
  "message": "Track not found",
  "timestamp": 1616161616161
}
```

## Implementation Notes

### Quality of Service (QoS)

The SDK uses the following QoS levels by default:

- State messages: QoS 0 (At most once)
- Command messages: QoS 1 (At least once)
- Response messages: QoS 1 (At least once)
- Connection messages: QoS 1 (At least once)

These can be configured in the client configuration.

### Retained Messages

The device may publish retained messages for the following topics:

- `state`: Last known state
- `connection`: Current connection status

This allows clients to get the latest state immediately upon subscription.

### Last Will and Testament (LWT)

The device should set up an LWT message for the `connection` topic with the status `offline`. This ensures that clients are notified if the device disconnects unexpectedly.

## Extending the Protocol

The protocol can be extended with additional commands and message types as needed. When adding new commands, follow these guidelines:

1. Use descriptive command names
2. Include all necessary parameters in the `params` object
3. Return appropriate data in the response
4. Document the new command and its parameters

## Testing MQTT Communication

You can use MQTT client tools like [MQTT Explorer](http://mqtt-explorer.com/) or [Mosquitto CLI](https://mosquitto.org/man/mosquitto_pub-1.html) to test the MQTT communication:

### Subscribe to all topics for a device

```bash
mosquitto_sub -h localhost -p 1883 -t "amora/devices/amora-player-001/#" -v
```

### Publish a command

```bash
mosquitto_pub -h localhost -p 1883 -t "amora/devices/amora-player-001/commands" -m '{"command":"play","commandId":"test-123","timestamp":1616161616161}'
```

### Monitor state updates

```bash
mosquitto_sub -h localhost -p 1883 -t "amora/devices/amora-player-001/state" -v
```
