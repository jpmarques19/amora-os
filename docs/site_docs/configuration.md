# AmoraOS Configuration Guide

This document provides detailed information about configuring AmoraOS for your specific needs.

## Configuration File

AmoraOS uses a JSON configuration file located at `edge/config/config.json`. This file contains all the settings needed to customize the behavior of the system.

### Basic Configuration Structure

```json
{
    "device": {
        "id": "waybox-player",
        "name": "Waybox Player"
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
    "dev_mode": false
}
```

## Configuration Sections

### Device Configuration

```json
"device": {
    "id": "waybox-player",
    "name": "Waybox Player"
}
```

- **id**: A unique identifier for your device. This is used for IoT Hub registration.
- **name**: A human-readable name for your device.

### MPD Configuration

```json
"mpd": {
    "host": "localhost",
    "port": 6600
}
```

- **host**: The hostname or IP address where MPD is running. Use "localhost" for the local machine.
- **port**: The port number MPD is listening on. The default is 6600.

### Content Configuration

```json
"content": {
    "storage_path": "/home/user/music",
    "playlists_path": "/home/user/music/playlists"
}
```

- **storage_path**: The directory where your music files are stored.
- **playlists_path**: The directory where playlists are stored.

### Audio Configuration

```json
"audio": {
    "backend": "pipewire",
    "device": "default",
    "volume": 80
}
```

- **backend**: The audio backend to use. Options include:
  - `pipewire`: Modern audio system with low latency (recommended)
  - `alsa`: Advanced Linux Sound Architecture
  - `pulse`: PulseAudio sound server
- **device**: The audio device to use. Use "default" for the system default device.
- **volume**: The initial volume level (0-100).

### Development Mode

```json
"dev_mode": false
```

- **dev_mode**: Set to `true` to enable development mode, which provides additional logging and debugging features.

## SDK Configuration

### MQTT Broker Configuration

```json
"broker": {
    "device_id": "amora-player-001",
    "broker_url": "mqtt.example.com",
    "port": 1883,
    "username": "username",
    "password": "password",
    "use_tls": false
}
```

- **device_id**: The unique identifier for your device in MQTT topics.
- **broker_url**: The hostname or IP address of the MQTT broker.
- **port**: The port number the MQTT broker is listening on (default: 1883, or 8883 for TLS).
- **username**: Optional username for MQTT broker authentication.
- **password**: Optional password for MQTT broker authentication.
- **use_tls**: Whether to use TLS encryption for MQTT communication.

### IoT Hub Configuration

```json
"iot": {
    "connection_string": "HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key",
    "telemetry_interval": 60,
    "enable_direct_methods": true,
    "enable_device_twin": true
}
```

- **connection_string**: The Azure IoT Hub connection string for your device.
- **telemetry_interval**: How often to send telemetry data to IoT Hub (in seconds).
- **enable_direct_methods**: Whether to enable direct method calls from IoT Hub.
- **enable_device_twin**: Whether to enable device twin synchronization.

## Environment Variables

You can override configuration settings using environment variables:

### Edge Application Environment Variables

- `WAYBOX_DEVICE_ID`: Override the device ID
- `WAYBOX_MPD_HOST`: Override the MPD host
- `WAYBOX_MPD_PORT`: Override the MPD port
- `WAYBOX_CONTENT_PATH`: Override the content storage path
- `WAYBOX_AUDIO_VOLUME`: Override the audio volume
- `WAYBOX_DEV_MODE`: Override the development mode setting

### SDK Environment Variables

- `AMORA_DEVICE_ID`: Device ID for MQTT topics
- `AMORA_MQTT_BROKER`: MQTT broker hostname or IP address
- `AMORA_MQTT_PORT`: MQTT broker port
- `AMORA_MQTT_USERNAME`: MQTT broker username
- `AMORA_MQTT_PASSWORD`: MQTT broker password
- `AMORA_MQTT_USE_TLS`: Whether to use TLS for MQTT (true/false)
- `AMORA_IOT_CONNECTION_STRING`: Azure IoT Hub connection string

Example:

```bash
export WAYBOX_DEVICE_ID="my-custom-player"
export WAYBOX_AUDIO_VOLUME=70
export AMORA_MQTT_BROKER="mqtt.example.com"
export AMORA_IOT_CONNECTION_STRING="HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key"
```

## Configuration Validation

AmoraOS uses Pydantic models to validate configuration. If your configuration is invalid, the application will log an error and exit.

Common validation errors:

- Volume outside the range 0-100
- Invalid audio backend
- Missing required fields
- Invalid paths for content storage

## Applying Configuration Changes

After modifying the configuration:

1. If running directly: Restart the application
   ```bash
   poetry run waybox-player restart
   ```

2. If running in a container: Restart the container
   ```bash
   docker restart waybox-player-python
   ```

## Configuration Examples

### Minimal Configuration

```json
{
    "device": {
        "id": "waybox-player"
    },
    "mpd": {
        "host": "localhost"
    },
    "content": {
        "storage_path": "/home/user/music"
    }
}
```

### Full Configuration with IoT and MQTT Integration

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
        "device": "hw:CARD=IQaudIODAC",
        "volume": 75
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
        "telemetry_interval": 60
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/waybox-player.log"
    },
    "dev_mode": false
}
```
