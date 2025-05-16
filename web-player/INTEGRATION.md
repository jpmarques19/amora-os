# Amora Web Player Integration Guide

This guide explains how to integrate the Amora Web Player with the Amora client SDK for production use.

## Overview

The Amora Web Player is designed to work with the Amora client SDK to communicate with the MQTT broker and control the music player. During development, a mock implementation of the SDK is used, but for production, the actual SDK should be integrated.

## Integration Steps

### 1. Build the Amora Client SDK

First, you need to build the Amora client SDK:

```bash
# Navigate to the client SDK directory
cd amora-sdk/client

# Install dependencies
npm install

# Build the SDK
npm run build
```

This will generate the compiled SDK files in the `dist` directory.

### 2. Include the SDK in the Web Player

Replace the mock SDK with the real one in the `index.html` file:

```html
<!-- Replace this line -->
<script src="js/amora-sdk-mock.js"></script>

<!-- With this line -->
<script src="path/to/amora-sdk.min.js"></script>
```

Make sure the path points to the correct location of the built SDK file.

### 3. Configure the MQTT Connection

The web player is already set up to connect to the MQTT broker using the configuration provided in the UI. Make sure your MQTT broker is:

- Running and accessible from the client's network
- Properly configured to accept connections from the web player
- Using the correct authentication if required

### 4. Test the Integration

After integrating the real SDK, test the web player to ensure it can:

- Connect to the MQTT broker
- Send commands to the player
- Receive status updates
- Display and control playlists

## SDK API Usage

The web player uses the following SDK APIs:

### Connection Management

```javascript
// Create client instance
const config = {
  brokerUrl: 'mqtt-broker-url',
  port: 1883,
  deviceId: 'amora-player-001',
  connectionOptions: {
    keepAlive: 60,
    cleanSession: true,
    reconnectOnFailure: true
  }
};

const amoraClient = new AmoraSDK.AmoraClient(config);

// Connect to the broker
await amoraClient.connect();

// Disconnect from the broker
await amoraClient.disconnect();
```

### Event Handling

```javascript
// Listen for connection status changes
amoraClient.on(AmoraSDK.EventType.CONNECTION_CHANGE, (status) => {
  // Handle connection status change
});

// Listen for player state changes
amoraClient.on(AmoraSDK.EventType.STATE_CHANGE, () => {
  // Handle state change
});

// Listen for position updates
amoraClient.on(AmoraSDK.EventType.POSITION_CHANGE, () => {
  // Handle position update
});

// Listen for volume changes
amoraClient.on(AmoraSDK.EventType.VOLUME_CHANGE, () => {
  // Handle volume change
});

// Listen for playlist changes
amoraClient.on(AmoraSDK.EventType.PLAYLIST_CHANGE, () => {
  // Handle playlist change
});

// Listen for errors
amoraClient.on(AmoraSDK.EventType.ERROR, (error) => {
  // Handle error
});
```

### Player Control

```javascript
// Play
await amoraClient.play();

// Pause
await amoraClient.pause();

// Stop
await amoraClient.stop();

// Next track
await amoraClient.next();

// Previous track
await amoraClient.previous();

// Set volume (0-100)
await amoraClient.setVolume(50);

// Set repeat mode
await amoraClient.setRepeat(true);

// Set random mode
await amoraClient.setRandom(true);
```

### Status and Playlist Management

```javascript
// Get current status
const status = await amoraClient.getStatus();

// Get available playlists
const playlists = await amoraClient.fetchPlaylists();

// Play a specific playlist
await amoraClient.playPlaylist('playlist-name');

// Play a specific track in the current playlist
await amoraClient.playTrack(trackIndex);
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the MQTT broker:

1. Check that the broker URL and port are correct
2. Verify that the broker is running and accessible from your network
3. Check if authentication is required and properly configured
4. Look for CORS issues if connecting from a different domain
5. Check browser console for any JavaScript errors

### Command Issues

If commands are not being sent or processed:

1. Verify that the device ID is correct
2. Check that the client is properly connected (connection status should be 'Connected')
3. Look for any error messages in the browser console
4. Verify that the MQTT topics are correctly configured in the SDK

### Status Update Issues

If status updates are not being received:

1. Check that the client is subscribed to the correct topics
2. Verify that the player device is publishing status updates
3. Check for any network issues that might prevent message delivery

## Advanced Configuration

For advanced configuration options, refer to the Amora client SDK documentation. The SDK supports various options for:

- TLS/SSL encryption
- Authentication methods
- Quality of Service (QoS) levels
- Reconnection strategies
- Custom topic prefixes

These can be configured through the `connectionOptions` parameter when creating the client instance.
