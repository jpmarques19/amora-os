# Amora Client SDK API Reference

This document provides detailed information about the Amora Client SDK API.

## Table of Contents

- [AmoraClient](#amoraclient)
- [Types and Interfaces](#types-and-interfaces)
- [Events](#events)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)

## AmoraClient

The `AmoraClient` class is the main entry point for the SDK. It provides methods for connecting to the MQTT broker, controlling the player, and receiving status updates.

### Constructor

```typescript
constructor(config: AmoraClientConfig)
```

Creates a new Amora client instance with the specified configuration.

**Parameters:**
- `config`: Configuration object for the client

### Configuration

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

interface ConnectionOptions {
  username?: string;        // Username for MQTT broker authentication
  password?: string;        // Password for MQTT broker authentication
  useTls?: boolean;         // Whether to use TLS for the connection
  caCertPath?: string;      // Path to CA certificate file for TLS
  clientCertPath?: string;  // Path to client certificate file for TLS
  clientKeyPath?: string;   // Path to client key file for TLS
  keepAlive?: number;       // Keep alive interval in seconds (default: 60)
  cleanSession?: boolean;   // Whether to use a clean session (default: true)
  reconnectOnFailure?: boolean;  // Whether to reconnect automatically (default: true)
  maxReconnectDelay?: number;    // Maximum reconnect delay in seconds (default: 300)
}

enum QoS {
  AT_MOST_ONCE = 0,
  AT_LEAST_ONCE = 1,
  EXACTLY_ONCE = 2
}
```

### Connection Methods

#### connect

```typescript
async connect(): Promise<void>
```

Connects to the MQTT broker and subscribes to the necessary topics.

**Returns:** Promise that resolves when connected

**Throws:** Error if connection fails

#### disconnect

```typescript
async disconnect(): Promise<void>
```

Disconnects from the MQTT broker.

**Returns:** Promise that resolves when disconnected

**Throws:** Error if disconnection fails

#### getConnectionStatus

```typescript
getConnectionStatus(): ConnectionStatus
```

Gets the current connection status.

**Returns:** Current connection status

```typescript
enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  ERROR = 'error'
}
```

### Player Status Methods

#### getPlayerStatus

```typescript
getPlayerStatus(): PlayerStatus
```

Gets the current player status.

**Returns:** Current player status

```typescript
interface PlayerStatus {
  state: PlayerState;       // Current player state
  currentSong?: SongMetadata;  // Current song metadata
  position?: number;        // Current playback position in seconds
  volume: number;           // Current volume (0-100)
  repeat: boolean;          // Whether repeat mode is enabled
  random: boolean;          // Whether random mode is enabled
}

enum PlayerState {
  PLAYING = 'playing',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  LOADING = 'loading',
  ERROR = 'error'
}

interface SongMetadata {
  title: string;            // Song title
  artist: string;           // Artist name
  album: string;            // Album name
  albumArt?: string;        // Album art URL
  duration: number;         // Song duration in seconds
  file: string;             // File path or URL
  [key: string]: any;       // Additional metadata
}
```

#### getPlaylists

```typescript
getPlaylists(): Playlist[]
```

Gets the available playlists.

**Returns:** Array of playlists

```typescript
interface Playlist {
  name: string;             // Playlist name
  items: PlaylistItem[];    // Playlist items
}

interface PlaylistItem extends SongMetadata {
  position: number;         // Position in the playlist
  isCurrent: boolean;       // Whether this is the current song
}
```

### Player Control Methods

#### play

```typescript
async play(): Promise<void>
```

Starts playback.

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### pause

```typescript
async pause(): Promise<void>
```

Pauses playback.

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### stop

```typescript
async stop(): Promise<void>
```

Stops playback.

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### next

```typescript
async next(): Promise<void>
```

Skips to the next track.

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### previous

```typescript
async previous(): Promise<void>
```

Goes back to the previous track.

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### setVolume

```typescript
async setVolume(volume: number): Promise<void>
```

Sets the volume.

**Parameters:**
- `volume`: Volume level (0-100)

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### setRepeat

```typescript
async setRepeat(repeat: boolean): Promise<void>
```

Sets repeat mode.

**Parameters:**
- `repeat`: Whether to enable repeat mode

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### setRandom

```typescript
async setRandom(random: boolean): Promise<void>
```

Sets random mode.

**Parameters:**
- `random`: Whether to enable random mode

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### getStatus

```typescript
async getStatus(): Promise<PlayerStatus>
```

Gets the current player status.

**Returns:** Promise that resolves with the current player status

**Throws:** Error if the command fails

#### fetchPlaylists

```typescript
async fetchPlaylists(): Promise<Playlist[]>
```

Gets the available playlists.

**Returns:** Promise that resolves with the available playlists

**Throws:** Error if the command fails

#### playPlaylist

```typescript
async playPlaylist(playlist: string): Promise<void>
```

Plays a playlist.

**Parameters:**
- `playlist`: Playlist name

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### playTrack

```typescript
async playTrack(trackIndex: number): Promise<void>
```

Plays a specific track.

**Parameters:**
- `trackIndex`: Track index in the current playlist

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### addTrack

```typescript
async addTrack(track: string, playlist?: string): Promise<void>
```

Adds a track to a playlist.

**Parameters:**
- `track`: Track to add
- `playlist`: Playlist to add to (optional, defaults to current playlist)

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### removeTrack

```typescript
async removeTrack(trackIndex: number, playlist?: string): Promise<void>
```

Removes a track from a playlist.

**Parameters:**
- `trackIndex`: Track index in the playlist
- `playlist`: Playlist to remove from (optional, defaults to current playlist)

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

#### reorderTrack

```typescript
async reorderTrack(fromIndex: number, toIndex: number, playlist?: string): Promise<void>
```

Reorders tracks in a playlist.

**Parameters:**
- `fromIndex`: Original position
- `toIndex`: New position
- `playlist`: Playlist to reorder (optional, defaults to current playlist)

**Returns:** Promise that resolves when the command is acknowledged

**Throws:** Error if the command fails

### Event Handling

The `AmoraClient` class extends `EventEmitter` and emits events when the player status changes.

#### on

```typescript
on(event: EventType, listener: EventListener): this
```

Registers an event listener.

**Parameters:**
- `event`: Event type
- `listener`: Event listener function

**Returns:** `this` for chaining

#### off

```typescript
off(event: EventType, listener: EventListener): this
```

Removes an event listener.

**Parameters:**
- `event`: Event type
- `listener`: Event listener function

**Returns:** `this` for chaining

## Types and Interfaces

### EventType

```typescript
enum EventType {
  STATE_CHANGE = 'stateChange',
  POSITION_CHANGE = 'positionChange',
  VOLUME_CHANGE = 'volumeChange',
  PLAYLIST_CHANGE = 'playlistChange',
  CONNECTION_CHANGE = 'connectionChange',
  COMMAND_RESPONSE = 'commandResponse',
  ERROR = 'error'
}
```

### EventListener

```typescript
type EventListener = (data: any) => void
```

### TopicType

```typescript
enum TopicType {
  STATE = 'state',
  COMMANDS = 'commands',
  RESPONSES = 'responses',
  CONNECTION = 'connection'
}
```

### CommandMessage

```typescript
interface CommandMessage {
  command: string;          // Command name
  commandId: string;        // Command ID
  params?: any;             // Command parameters
  timestamp: number;        // Timestamp
}
```

### ResponseMessage

```typescript
interface ResponseMessage {
  commandId: string;        // Command ID that this response is for
  result: boolean;          // Whether the command was successful
  message: string;          // Response message
  data?: any;               // Response data
  timestamp: number;        // Timestamp
}
```

### StateMessage

```typescript
interface StateMessage {
  state: PlayerState;       // Player state
  currentSong?: SongMetadata;  // Current song
  position?: number;        // Current position
  volume: number;           // Current volume
  repeat: boolean;          // Whether repeat mode is enabled
  random: boolean;          // Whether random mode is enabled
  timestamp: number;        // Timestamp
}
```

## Events

The SDK emits the following events:

### STATE_CHANGE

Emitted when the player state changes.

**Data:** New player state (`PlayerState`)

### POSITION_CHANGE

Emitted when the playback position changes.

**Data:** New position in seconds (`number`)

### VOLUME_CHANGE

Emitted when the volume changes.

**Data:** New volume level (`number`)

### PLAYLIST_CHANGE

Emitted when the playlists change.

**Data:** Updated playlists (`Playlist[]`)

### CONNECTION_CHANGE

Emitted when the connection status changes.

**Data:** New connection status (`ConnectionStatus`)

### COMMAND_RESPONSE

Emitted when a command response is received.

**Data:** Command response (`ResponseMessage`)

### ERROR

Emitted when an error occurs.

**Data:** Error object (`Error`)

## Error Handling

The SDK provides comprehensive error handling through both promises and events.

### Promise-based Error Handling

All asynchronous methods return promises that reject with an error if the operation fails.

```javascript
client.play().catch(error => {
  console.error('Error playing:', error.message);
});
```

### Event-based Error Handling

The SDK also emits `ERROR` events when errors occur.

```javascript
client.on(EventType.ERROR, error => {
  console.error('Error:', error.message);
});
```

## Advanced Usage

### Using the MQTTClient Directly

For advanced use cases, you can use the `MQTTClient` class directly.

```javascript
const { MQTTClient, QoS } = require('amora-client-sdk');

const mqttClient = new MQTTClient({
  brokerUrl: 'localhost',
  port: 1883,
  clientId: 'my-client',
  defaultQoS: QoS.AT_LEAST_ONCE
});

mqttClient.on('message', (topic, payload) => {
  console.log(`Received message on topic ${topic}: ${payload.toString()}`);
});

await mqttClient.connect();
await mqttClient.subscribe('my/topic');
await mqttClient.publish('my/topic', 'Hello, world!');
await mqttClient.disconnect();
```

### Using the TopicManager

The `TopicManager` class helps manage MQTT topics.

```javascript
const { TopicManager, TopicType } = require('amora-client-sdk');

const topicManager = new TopicManager('amora/devices', 'my-device');

// Get a topic string
const stateTopic = topicManager.getTopic(TopicType.STATE);
console.log(stateTopic);  // 'amora/devices/my-device/state'

// Get subscription topics
const subscriptionTopics = topicManager.getSubscriptionTopics();
console.log(subscriptionTopics);  // ['amora/devices/my-device/state', 'amora/devices/my-device/responses']

// Parse a topic
const topicType = topicManager.parseTopic('amora/devices/my-device/state');
console.log(topicType);  // 'state'
```

### Creating Messages

The SDK provides utility functions for creating messages.

```javascript
const { createCommandMessage, createStateMessage, PlayerState } = require('amora-client-sdk');

// Create a command message
const commandMessage = createCommandMessage('play', { trackId: '123' });
console.log(commandMessage);
// {
//   command: 'play',
//   commandId: '550e8400-e29b-41d4-a716-446655440000',
//   params: { trackId: '123' },
//   timestamp: 1616161616161
// }

// Create a state message
const stateMessage = createStateMessage(
  PlayerState.PLAYING,
  {
    title: 'My Song',
    artist: 'My Artist',
    album: 'My Album',
    duration: 180
  },
  60,
  80,
  false,
  false
);
console.log(stateMessage);
// {
//   state: 'playing',
//   currentSong: {
//     title: 'My Song',
//     artist: 'My Artist',
//     album: 'My Album',
//     duration: 180
//   },
//   position: 60,
//   volume: 80,
//   repeat: false,
//   random: false,
//   timestamp: 1616161616161
// }
```
