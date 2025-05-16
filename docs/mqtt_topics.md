# MQTT Topics for Amora Device SDK

This document describes the MQTT topics used for communication between Amora devices and clients.

## Topic Structure

All MQTT topics follow this structure:

```
{topic_prefix}/{device_id}/{topic_type}
```

Where:
- `topic_prefix`: The prefix for all topics (default: "amora/devices")
- `device_id`: The unique identifier for the device
- `topic_type`: The type of topic (state, commands, responses, connection)

## Topic Types

The Amora Device SDK uses the following topic types:

### State Topic

**Format**: `{topic_prefix}/{device_id}/state`

**Purpose**: Publishes the current state of the device, including player status.

**Direction**: Device → Client

**QoS**: 1 (At least once)

**Retain**: True

**Payload Example**:
```json
{
  "timestamp": 1623456789.123,
  "state": "play",
  "current_song": {
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "file": "path/to/song.mp3",
    "duration": 180.5,
    "position": 45.2
  },
  "volume": 75,
  "playlist": "My Playlist",
  "playlist_tracks": [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "file": "path/to/song.mp3"
    },
    {
      "title": "Another Song",
      "artist": "Another Artist",
      "album": "Another Album",
      "file": "path/to/another-song.mp3"
    }
  ],
  "repeat": false,
  "random": false
}
```

### Commands Topic

**Format**: `{topic_prefix}/{device_id}/commands`

**Purpose**: Sends commands to the device.

**Direction**: Client → Device

**QoS**: 1 (At least once)

**Retain**: False

**Payload Example**:
```json
{
  "timestamp": 1623456789.123,
  "command": "play",
  "command_id": "550e8400-e29b-41d4-a716-446655440000",
  "params": {
    "playlist": "My Playlist"
  }
}
```

### Responses Topic

**Format**: `{topic_prefix}/{device_id}/responses`

**Purpose**: Publishes responses to commands.

**Direction**: Device → Client

**QoS**: 1 (At least once)

**Retain**: False

**Payload Example**:
```json
{
  "timestamp": 1623456789.123,
  "command_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": true,
  "message": "Command play executed",
  "data": {
    "result": true
  }
}
```

### Connection Topic

**Format**: `{topic_prefix}/{device_id}/connection`

**Purpose**: Publishes the connection status of the device.

**Direction**: Device → Client

**QoS**: 1 (At least once)

**Retain**: True

**Payload Example**:
```json
{
  "timestamp": 1623456789.123,
  "status": "online"
}
```

## Player Status Updates

The Amora Device SDK provides real-time player status updates through the state topic. These updates include:

1. **Current track playback time/position**: The `current_song.position` field in the state message is updated in real-time as the track plays.

2. **Playback state**: The `state` field indicates the current playback state (play, pause, stop).

3. **List of tracks in the playlist**: The `playlist_tracks` field contains the list of tracks in the current playlist.

4. **Track metadata**: The `current_song` field includes metadata such as title, artist, album, file path, duration, and position.

### Update Frequency

The player status is updated in the following scenarios:

1. **Position updates**: When a track is playing, position updates are sent at regular intervals (default: 1 second).

2. **State changes**: When the playback state changes (play, pause, stop), a full status update is sent immediately.

3. **Track changes**: When the current track changes, a full status update is sent immediately.

4. **Volume changes**: When the volume changes, a status update is sent immediately.

5. **Periodic full updates**: Full status updates are sent periodically (default: every 5 seconds) regardless of changes.

## Subscribing to Topics

Clients should subscribe to the following topics to receive updates from the device:

```
{topic_prefix}/{device_id}/state
{topic_prefix}/{device_id}/responses
{topic_prefix}/{device_id}/connection
```

For convenience, clients can use a wildcard subscription:

```
{topic_prefix}/{device_id}/#
```

## Publishing Commands

Clients should publish commands to the commands topic:

```
{topic_prefix}/{device_id}/commands
```

## Available Commands

The following commands are available:

- `play`: Start or resume playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Skip to the next track
- `previous`: Skip to the previous track
- `set_volume`: Set the volume level (params: `{"volume": 75}`)
- `play_playlist`: Play a specific playlist (params: `{"playlist": "My Playlist"}`)
- `set_repeat`: Set repeat mode (params: `{"repeat": true}`)
- `set_random`: Set random mode (params: `{"random": true}`)
- `create_playlist`: Create a new playlist (params: `{"name": "New Playlist", "files": ["path/to/song.mp3"]}`)
- `delete_playlist`: Delete a playlist (params: `{"playlist": "My Playlist"}`)
- `get_playlists`: Get available playlists
- `get_playlist_songs`: Get songs in a playlist (params: `{"playlist": "My Playlist"}`)
- `update_database`: Update the music database
