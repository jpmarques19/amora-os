# AmoraSDK

AmoraSDK is a client-server SDK for controlling the AmoraOS player device and receiving real-time status updates using MQTT broker for real-time communication and Azure IoT Hub for device management.

## Features

- Control player device (play, pause, next, prev, stop)
- Get real-time status updates from the player
- List available tracks and playlists
- MQTT broker for real-time communication
- Azure IoT Hub integration for device management
- Simple React test app for demonstration

## Architecture

The SDK consists of two main components:

1. **Device SDK (Python)**: Runs on the player device and provides:
   - MQTT broker client for real-time communication
   - Azure IoT Hub device client for device management
   - Device twin for configuration synchronization
   - Telemetry for device status reporting
   - Interface to the player implementation

2. **Client SDK (TypeScript/JavaScript)**: Used by client applications to:
   - Connect to MQTT broker for real-time communication
   - Connect to Azure IoT Hub for device management
   - Send commands to the device
   - Receive real-time status updates
   - Provide a simple interface for controlling the player

## Installation

### Device SDK

```bash
cd sdk
poetry install
```

### Client SDK

```bash
cd sdk/client
npm install
```

## Usage

### Device SDK

```python
import asyncio
from amora_sdk.device import DeviceClient
from amora_sdk.device.broker import BrokerConfig
from amora_sdk.device.iot import IoTConfig
from amora_sdk.device.player import PlayerInterface

# Create player interface
player = PlayerInterface({
    "mpd": {
        "host": "localhost",
        "port": 6600
    },
    "content": {
        "storage_path": "/home/user/music",
        "playlists_path": "/home/user/music/playlists"
    },
    "audio": {
        "backend": "pipewire",
        "device": "default",
        "volume": 80
    }
})

# Connect to player
player.connect()

# Configure broker for real-time communication
broker_config = BrokerConfig(
    device_id="amora-player-001",
    broker_url="mqtt.example.com",
    port=1883
)

# Configure IoT Hub for device management
iot_config = IoTConfig(
    connection_string="YOUR_DEVICE_CONNECTION_STRING"
)

# Create device client
device_client = DeviceClient(
    player_interface=player,
    broker_config=broker_config,
    iot_config=iot_config
)

async def main():
    # Connect to services
    await device_client.connect()

    # Start the client
    await device_client.start()

    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        # Clean up
        await device_client.stop()
        player.disconnect()

# Run the client
asyncio.run(main())
```

### Client SDK

```typescript
import { AmoraClient } from 'amora-sdk-client';

// Create client instance
const client = new AmoraClient({
  mqtt: {
    brokerUrl: 'mqtt://mqtt.example.com:1883',
    clientId: 'amora-client-001',
    username: 'username',
    password: 'password'
  },
  iot: {
    connectionString: 'YOUR_IOT_HUB_CONNECTION_STRING',
    deviceId: 'amora-player-001'
  }
});

// Connect to services
await client.connect();

// Listen for status updates
client.onStatusUpdate((status) => {
  console.log('Player status:', status);
});

// Listen for connection status
client.onConnectionStatus((connected) => {
  console.log('Device connection status:', connected ? 'online' : 'offline');
});

// Control the player
await client.play();
await client.pause();
await client.next();
await client.previous();
await client.stop();
await client.setVolume(80);

// Disconnect when done
await client.disconnect();
```

## Test App

The SDK includes a simple React test app for demonstration purposes. To run the test app:

```bash
cd sdk/test_app
npm install
npm start
```

## API Reference

### Device SDK

- `DeviceClient`: Main device client class
  - `connect()`: Connect to all services
  - `disconnect()`: Disconnect from all services
  - `start()`: Start the client
  - `stop()`: Stop the client

- `BrokerManager`: MQTT broker manager
  - `connect()`: Connect to MQTT broker
  - `disconnect()`: Disconnect from MQTT broker
  - `publish_state()`: Publish device state
  - `publish_response()`: Publish command response
  - `update_player_state()`: Update and publish player state

- `IoTDeviceClient`: IoT Hub client for device management
  - `connect()`: Connect to IoT Hub
  - `disconnect()`: Disconnect from IoT Hub
  - `start()`: Start the client
  - `stop()`: Stop the client
  - `send_message()`: Send telemetry message
  - `patch_twin_reported_properties()`: Update device twin

- `PlayerInterface`: Player interface class
  - `connect()`: Connect to the player
  - `disconnect()`: Disconnect from the player
  - `play()`: Start or resume playback
  - `pause()`: Pause playback
  - `stop()`: Stop playback
  - `next()`: Skip to next track
  - `previous()`: Skip to previous track
  - `set_volume(volume)`: Set volume level
  - `get_status()`: Get current player status
  - `get_playlists()`: Get available playlists

### Client SDK

- `AmoraClient`: Main client class
  - `connect()`: Connect to all services
  - `disconnect()`: Disconnect from all services
  - `onStatusUpdate(callback)`: Register callback for status updates
  - `onConnectionStatus(callback)`: Register callback for connection status changes
  - `play()`: Start or resume playback
  - `pause()`: Pause playback
  - `stop()`: Stop playback
  - `next()`: Skip to next track
  - `previous()`: Skip to previous track
  - `setVolume(volume)`: Set volume level
  - `getStatus()`: Get current player status
  - `getPlaylists()`: Get available playlists

- `MQTTClient`: MQTT client for real-time communication
  - `connect()`: Connect to MQTT broker
  - `disconnect()`: Disconnect from MQTT broker
  - `subscribe(topic, callback)`: Subscribe to a topic
  - `publish(topic, message)`: Publish a message

- `IoTClient`: IoT Hub client for device management
  - `connect()`: Connect to IoT Hub
  - `disconnect()`: Disconnect from IoT Hub
  - `invokeMethod(deviceId, methodName, payload)`: Invoke a direct method
  - `updateTwin(deviceId, properties)`: Update device twin

## Documentation

For more detailed documentation, see the [docs](docs/) directory:

- [Architecture](docs/architecture.md) - Overview of the SDK architecture
- [MQTT Integration](docs/mqtt_integration.md) - Guide for MQTT broker integration
- [Azure Integration](docs/iot_integration.md) - Guide for Azure IoT Hub integration
- [Client Development](docs/client_development.md) - Guide for developing client applications
- [Device Integration](docs/device_integration.md) - Guide for integrating with devices
