# Amora Client SDK

A TypeScript/JavaScript SDK for controlling Amora music player devices through MQTT.

## Features

- Real-time status updates from the music player to the web app:
  - Player state monitoring (playing, stopped, paused)
  - Track playback position tracking (current time/duration)
  - Track metadata retrieval (artist, title, album, cover art)
  - Complete playlist management with all available tracks and their metadata

- Control commands from the web app to the music player:
  - Play/Pause/Stop controls
  - Next/Previous track navigation
  - Track selection from playlist
  - Playlist manipulation (add/remove tracks, reorder)

- Simple and intuitive API for web developers
- Comprehensive error handling and connection management
- Proper TypeScript typing for all public interfaces
- Abstracts all MQTT communication complexity

## Installation

```bash
npm install amora-client-sdk
```

## Quick Start

```javascript
const { AmoraClient, EventType } = require('amora-client-sdk');

// Create client configuration
const config = {
  brokerUrl: 'localhost',
  port: 1883,
  deviceId: 'amora-player-001'
};

// Create client instance
const client = new AmoraClient(config);

// Set up event listeners
client.on(EventType.STATE_CHANGE, (state) => {
  console.log(`Player state changed: ${state}`);
});

// Connect to the MQTT broker
async function run() {
  try {
    await client.connect();
    console.log('Connected!');

    // Control the player
    await client.play();

    // Wait for 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Disconnect when done
    await client.disconnect();
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the example
run();
```

## API Reference

### AmoraClient

The main client class for interacting with Amora music player devices.

#### Constructor

```typescript
constructor(config: AmoraClientConfig)
```

Creates a new Amora client instance with the specified configuration.

#### Configuration

```typescript
interface AmoraClientConfig {
  brokerUrl: string;        // MQTT broker URL
  port: number;             // MQTT broker port
  clientId?: string;        // Client ID (auto-generated if not provided)
  deviceId: string;         // Device ID to connect to
  topicPrefix?: string;     // Topic prefix (default: 'amora/devices')
  connectionOptions?: ConnectionOptions;  // Connection options
  defaultQoS?: QoS;         // Default QoS level (default: AT_LEAST_ONCE)
}
```

#### Connection Methods

- `connect()`: Connect to the MQTT broker
- `disconnect()`: Disconnect from the MQTT broker
- `getConnectionStatus()`: Get the current connection status

#### Player Control Methods

- `play()`: Start playback
- `pause()`: Pause playback
- `stop()`: Stop playback
- `next()`: Skip to the next track
- `previous()`: Go back to the previous track
- `setVolume(volume: number)`: Set the volume (0-100)
- `getVolume()`: Get the current volume
- `setRepeat(repeat: boolean)`: Set repeat mode
- `setRandom(random: boolean)`: Set random mode
- `getStatus()`: Get the current player status
- `getPlaylists()`: Get the available playlists
- `playPlaylist(playlist: string)`: Play a playlist
- `getPlaylistSongs(playlist: string)`: Get songs in a playlist
- `createPlaylist(name: string, files: string[])`: Create a new playlist
- `deletePlaylist(playlist: string)`: Delete a playlist
- `updateDatabase()`: Update the music database
- `playTrack(trackIndex: number)`: Play a specific track
- `addTrack(track: string, playlist: string)`: Add a track to a playlist
- `removeTrack(trackIndex: number, playlist: string)`: Remove a track from a playlist
- `reorderTrack(fromIndex: number, toIndex: number, playlist: string)`: Reorder tracks in a playlist

#### Event Handling

```typescript
client.on(EventType.STATE_CHANGE, (state) => {
  console.log(`Player state changed: ${state}`);
});
```

Available event types:
- `STATE_CHANGE`: Player state changed
- `POSITION_CHANGE`: Playback position changed
- `VOLUME_CHANGE`: Volume changed
- `PLAYLIST_CHANGE`: Playlists updated
- `CONNECTION_CHANGE`: Connection status changed
- `COMMAND_RESPONSE`: Command response received
- `ERROR`: Error occurred

## Examples

See the `examples` directory for more detailed examples:

- `basic-usage.js`: Basic usage example

## MQTT Topics

The SDK uses the following MQTT topics for communication:

- `{topicPrefix}/{deviceId}/state`: Player state updates
- `{topicPrefix}/{deviceId}/commands`: Commands to the player
- `{topicPrefix}/{deviceId}/responses`: Command responses from the player
- `{topicPrefix}/{deviceId}/connection`: Connection status updates

## Development

### Building the SDK

```bash
npm install
npm run build
```

### Running Tests

```bash
npm test
```

### Generating Documentation

```bash
npm run docs
```

## License

MIT
