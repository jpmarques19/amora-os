# AmoraOS IoT Integration Guide

This guide provides information about the IoT integration features of AmoraOS, which enable remote device management, monitoring, and diagnostics through Azure IoT Hub.

## Architecture Overview

In the AmoraOS architecture:

- **Azure IoT Hub**: Serves as a control layer for device management, diagnostics, and low-level operations
- **MQTT Broker**: Handles real-time communication between devices and client applications

## Azure IoT Hub Integration

AmoraOS integrates with Azure IoT Hub to provide the following capabilities:

- Remote device management and monitoring
- Device configuration through device twins
- Diagnostics and low-level operations
- Telemetry reporting for device status
- Content synchronization from Azure Blob Storage

## MQTT Broker Integration

In addition to Azure IoT Hub, AmoraOS uses an MQTT broker for real-time communication:

- Real-time status updates via MQTT topics
- Command handling via MQTT topics
- Automatic reconnection with exponential backoff
- Last Will and Testament for connection status

## Setting Up Azure IoT Hub

### 1. Create an Azure IoT Hub

1. Sign in to the [Azure Portal](https://portal.azure.com)
2. Create a new IoT Hub resource
3. Select the appropriate tier (Free tier is sufficient for testing)
4. Complete the creation process

### 2. Register Your Device

1. Navigate to your IoT Hub in the Azure Portal
2. Go to "IoT devices" under "Device management"
3. Click "Add" to register a new device
4. Enter your device ID (e.g., "waybox-player-001")
5. Save the device

### 3. Get the Connection String

1. Click on your newly registered device
2. Copy the "Primary Connection String"
3. This string will be used in your AmoraOS configuration

## Setting Up MQTT Broker

### 1. Choose an MQTT Broker

You can use any MQTT broker that supports MQTT 3.1.1 or later:

- [Mosquitto](https://mosquitto.org/) (open-source, lightweight)
- [HiveMQ](https://www.hivemq.com/) (scalable, enterprise-ready)
- [EMQ X](https://www.emqx.io/) (high-performance, cloud-native)
- [Azure IoT Hub](https://azure.microsoft.com/services/iot-hub/) (using MQTT protocol)

### 2. Configure the Broker

For Mosquitto:

1. Install Mosquitto:
   ```bash
   sudo apt install mosquitto mosquitto-clients
   ```

2. Configure authentication (optional):
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   ```

   Add:
   ```
   allow_anonymous false
   password_file /etc/mosquitto/passwd
   ```

3. Create a password file:
   ```bash
   sudo mosquitto_passwd -c /etc/mosquitto/passwd username
   ```

4. Restart Mosquitto:
   ```bash
   sudo systemctl restart mosquitto
   ```

## Configuring AmoraOS for IoT Integration

Update your `config.json` file to include the IoT and MQTT configuration:

```json
{
    "device": {
        "id": "waybox-player-001",
        "name": "Living Room Player"
    },
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
    },
    "broker": {
        "device_id": "amora-player-001",
        "broker_url": "mqtt.example.com",
        "port": 1883,
        "username": "username",
        "password": "password",
        "use_tls": false
    },
    "iot": {
        "connection_string": "HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key",
        "telemetry_interval": 60,
        "enable_direct_methods": true,
        "enable_device_twin": true
    },
    "dev_mode": false
}
```

## IoT Features

### Device Twins

Device twins provide a way to synchronize state between your device and IoT Hub:

- **Reported Properties**: Properties reported by the device to IoT Hub
  - Current playback status
  - Volume level
  - Connected audio device
  - Available storage space
  - Current playlist
  - Software version

- **Desired Properties**: Properties set in IoT Hub to configure the device
  - Volume settings
  - Default playlist
  - Audio device configuration
  - Content synchronization settings

Example device twin JSON:

```json
{
    "deviceId": "waybox-player-001",
    "properties": {
        "desired": {
            "audio": {
                "volume": 75,
                "device": "default"
            },
            "content": {
                "default_playlist": "relaxing",
                "sync_enabled": true
            },
            "$metadata": {...},
            "$version": 4
        },
        "reported": {
            "audio": {
                "volume": 75,
                "device": "hw:CARD=IQaudIODAC",
                "backend": "pipewire"
            },
            "playback": {
                "status": "playing",
                "current_track": "Relaxing Piano.mp3",
                "position": 145,
                "duration": 320
            },
            "system": {
                "version": "1.0.0",
                "uptime": 86400,
                "free_space": 10240
            },
            "$metadata": {...},
            "$version": 7
        }
    }
}
```

### Direct Methods

Direct methods allow you to remotely control your device:

| Method Name | Description | Parameters |
|-------------|-------------|------------|
| `play` | Start playback | None |
| `pause` | Pause playback | None |
| `stop` | Stop playback | None |
| `next` | Play next track | None |
| `previous` | Play previous track | None |
| `setVolume` | Set volume level | `{"volume": 75}` |
| `loadPlaylist` | Load a playlist | `{"playlist": "relaxing"}` |
| `syncContent` | Trigger content sync | `{"force": true}` |
| `reboot` | Reboot the device | None |

Example direct method call (using Azure CLI):

```bash
az iot hub invoke-device-method --hub-name YourIoTHub --device-id waybox-player-001 --method-name play
```

### MQTT Topics

The SDK uses a structured topic hierarchy for communication:

```
amora/devices/{device_id}/commands    # Commands from clients to device
amora/devices/{device_id}/responses   # Command responses from device to clients
amora/devices/{device_id}/state       # State updates from device to clients
amora/devices/{device_id}/connection  # Connection status (online/offline)
```

### Testing MQTT Communication

You can test MQTT communication using the Mosquitto client tools:

```bash
# Subscribe to state updates
mosquitto_sub -h mqtt.example.com -t "amora/devices/amora-player-001/state"

# Send a command
mosquitto_pub -h mqtt.example.com -t "amora/devices/amora-player-001/commands" -m '{"command":"play","command_id":"test-1","params":{},"timestamp":1620000000}'
```

## Troubleshooting IoT Connectivity

- **Connection Issues**: Verify your connection string and network connectivity
- **Authentication Errors**: Check that your device is properly registered in IoT Hub
- **Message Delivery Failures**: Ensure your telemetry format is correct
- **Twin Synchronization Problems**: Check for JSON formatting errors in reported properties
- **MQTT Connection Issues**: Verify broker address and credentials
- **MQTT Subscription Issues**: Check topic permissions and format

## Security Considerations

- Store connection strings securely
- Use X.509 certificate authentication for production deployments
- Implement device-level encryption for sensitive data
- Regularly update the device firmware
- Monitor for unusual connection patterns
- Use TLS for MQTT communication in production
- Implement proper authentication for MQTT broker
