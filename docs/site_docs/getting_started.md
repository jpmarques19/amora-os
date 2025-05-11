# Getting Started with AmoraOS

This guide will help you set up and start using AmoraOS, an IoT Edge Audio Platform and SDK for Raspberry Pi music boxes.

## Prerequisites

Before you begin, ensure you have the following:

- **Hardware**:
  - Raspberry Pi 4 (recommended) or Raspberry Pi 3B+
  - IQUADIO PI DA audio HAT (optional but recommended for high-quality audio)
  - SD card (16GB or larger)
  - Power supply for Raspberry Pi
  - Speakers or headphones

- **Software**:
  - Debian Bookworm installed on your Raspberry Pi
  - Git
  - Docker (for containerized deployment)
  - Python 3.10 or higher
  - Poetry (for dependency management)

## Installation Options

You can install AmoraOS in two ways:

1. **Direct Installation**: Install directly on a Debian Bookworm system
2. **Containerized Deployment**: Run in a Docker container (recommended)

## Direct Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/amora-os.git
cd amora-os/edge
```

### 2. Install Dependencies with Poetry

```bash
# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 3. Configure the Application

Edit the configuration file in `edge/config/config.json` to match your setup:

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
        "storage_path": "/path/to/your/music",
        "playlists_path": "/path/to/your/music/playlists"
    },
    "audio": {
        "backend": "pipewire",
        "device": "default",
        "volume": 80
    },
    "dev_mode": false
}
```

### 4. Run the Application

```bash
# Start the player
poetry run waybox-player start

# Test audio functionality
poetry run waybox-player test-audio
```

## Containerized Deployment (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/amora-os.git
cd amora-os
```

### 2. Build the Docker Image

```bash
cd edge
docker build -t waybox-python-player .
```

### 3. Run the Container

For production use:

```bash
docker run -d --name waybox-player-python --privileged --network host \
  -v ./music:/home/user/music \
  --device /dev/snd:/dev/snd \
  --group-add audio \
  waybox-python-player
```

For development use:

```bash
docker run -d --name waybox-player-python-dev --privileged --network host \
  -v ./samples:/home/user/music \
  -v ./src:/home/user/app/src \
  -v ./config:/home/user/app/config \
  -v ./scripts:/home/user/app/scripts \
  --device /dev/snd:/dev/snd \
  --group-add audio \
  waybox-python-player python3 -m src.main start --dev
```

## SDK Installation

To use the AmoraSDK for device integration:

### 1. Install the SDK

```bash
cd amora-os/sdk
poetry install
```

### 2. Configure the SDK

Create a configuration file for the SDK:

```python
from amora_sdk.device import DeviceClient
from amora_sdk.device.broker import BrokerConfig
from amora_sdk.device.iot import IoTConfig

# MQTT broker configuration
broker_config = BrokerConfig(
    device_id="amora-player-001",
    broker_url="mqtt.example.com",
    port=1883
)

# IoT Hub configuration
iot_config = IoTConfig(
    connection_string="HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key"
)

# Create device client
device_client = DeviceClient(
    player_interface=player,
    broker_config=broker_config,
    iot_config=iot_config
)

# Start device client
await device_client.start()
```

## Linux-Only Development

This project is now exclusively developed and maintained for Linux systems. Windows development is no longer supported.

## Testing Your Installation

### Test Audio Playback

```bash
# Using the CLI
poetry run waybox-player test-audio

# Or directly with Python
python -m src.main test-audio
```

### Using Sample Music Files

1. Add MP3 files to the `samples` directory
2. Create playlists by adding files to `samples/playlists/[playlist_name]`
3. Update the MPD database and start playback:

```bash
# If using the container in dev mode
/home/user/app/scripts/play-sample.sh
```

## Testing the SDK

To test the SDK functionality:

```bash
cd amora-os/sdk
poetry run pytest tests/
```

For integration tests that require Azure IoT Hub:

```bash
# Set environment variables for IoT Hub connection
export AMORA_IOT_CONNECTION_STRING="HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key"

# Run integration tests
poetry run pytest integration_tests/
```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about all configuration options
- [Developer Guide](developer_guide.md) - Detailed information for developers
- [IoT Integration](iot_integration.md) - How to connect to Azure IoT Hub
- [Architecture](architecture.md) - Overview of the AmoraSDK architecture
- [Data Flow](data_flow.md) - Data flow between components
