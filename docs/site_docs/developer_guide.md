# AmoraOS Developer Guide

This guide provides detailed information for developers working with AmoraOS, including architecture, code organization, and best practices.

## Architecture Overview

AmoraOS follows a modular architecture with containerized components on edge devices connecting to Azure IoT Hub:

![AmoraOS Architecture](./images/amora-os-overview.jpeg)

### Key Components

- **Edge Device**: Raspberry Pi running Debian Bookworm with containerized components
- **Python App**: Main application logic handling device-side operations
- **Music Player Daemon (MPD)**: Handles audio playback and playlist management
- **Azure IoT SDK**: Manages cloud connectivity, device twins, and commands
- **MQTT Broker**: Enables real-time communication between devices and client applications
- **Raspberry Pi & IQAUDIO DAC**: Hardware platform for high-quality audio at the edge

## Project Structure

```
amora-os/
├── edge/              # Edge device implementation
│   ├── src/           # Core application code
│   │   ├── main.py    # Entry point and CLI
│   │   ├── player.py  # Player implementation
│   │   └── utils.py   # Utility functions
│   ├── config/        # Configuration files
│   ├── scripts/       # Utility scripts
│   ├── samples/       # Sample music for testing
│   ├── tests/         # Edge device test suite
│   ├── Dockerfile     # Container definition
│   └── pyproject.toml # Poetry project definition
├── sdk/               # AmoraSDK for application integration
│   ├── amora_sdk/     # Core SDK code
│   │   ├── device/    # Device-side SDK implementation
│   │   │   ├── broker/  # MQTT broker communication
│   │   │   ├── iot/     # Azure IoT Hub integration
│   │   │   └── player/  # Music player implementation
│   │   └── __init__.py  # SDK entry point
│   ├── tests/         # Unit tests
│   └── integration_tests/ # Integration tests
├── docs/              # Documentation
│   └── images/        # Architecture diagrams
└── .gitignore         # Git ignore file
```

## Development Environment Setup

### Local Development with Poetry

1. **Install Poetry**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Dependencies**:
   ```bash
   cd edge
   poetry install
   ```

3. **Activate the Virtual Environment**:
   ```bash
   poetry shell
   ```

4. **Run the Application**:
   ```bash
   waybox-player start --dev
   ```

### Linux-Only Development

This project is now exclusively developed and maintained for Linux systems. Windows development is no longer supported.

## Code Organization

### Main Module

The main module (`src/main.py`) serves as the entry point with a CLI interface using Click:

```python
import click
from .player import MusicPlayer
from .utils import detect_audio_devices

@click.group()
def cli():
    """Waybox Player CLI."""
    pass

@cli.command()
@click.option("--dev", is_flag=True, help="Run in development mode")
def start(dev):
    """Start the player."""
    # Implementation...

@cli.command()
def test_audio():
    """Test audio functionality."""
    # Implementation...

if __name__ == "__main__":
    cli()
```

### Player Module

The player module (`src/player.py`) contains the core functionality for MPD control and playback:

```python
class MusicPlayer:
    def __init__(self, config):
        self.config = config
        self.client = None

    def connect(self):
        """Connect to MPD server."""
        # Implementation...

    def play(self):
        """Start playback."""
        # Implementation...

    # Other methods...
```

### Utils Module

The utils module (`src/utils.py`) provides audio device detection and configuration utilities:

```python
def detect_audio_devices():
    """Detect available audio devices."""
    # Implementation...

def configure_audio_device(device, backend):
    """Configure the specified audio device."""
    # Implementation...
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_player.py
```

### Writing Tests

Tests are located in the `edge/tests` directory. Use pytest for writing tests:

```python
# tests/test_player.py
import pytest
from src.player import MusicPlayer

def test_player_initialization():
    config = {
        "mpd": {"host": "localhost", "port": 6600},
        "content": {"storage_path": "/tmp/music"}
    }
    player = MusicPlayer(config)
    assert player.config == config
    assert player.client is None
```

## Docker Development

### Building the Docker Image

```bash
cd edge
docker build -t waybox-python-player .
```

### Running in Development Mode

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

### Debugging in the Container

```bash
# Attach to the running container
docker exec -it waybox-player-python-dev bash

# Check logs
docker logs waybox-player-python-dev

# Run a specific command in the container
docker exec waybox-player-python-dev python3 -m src.main test-audio
```

## Dependency Management

- **Poetry** is used for development on the host machine
- In the Docker container, we use a Python virtual environment with pip
- When adding or updating dependencies:
  1. Add them to pyproject.toml with Poetry:
     ```bash
     poetry add package-name
     ```
  2. Update the Dockerfile to include the new dependency in the pip install command
  3. Rebuild the container to apply the changes

## Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Document classes and functions with docstrings
- Write unit tests for new functionality
- Keep functions small and focused on a single responsibility

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## IoT Integration Development

The IoT integration is implemented using the Azure IoT Device SDK for Python and MQTT broker for real-time communication:

1. **Azure IoT Hub Integration**:
   - Device twin synchronization for configuration
   - Direct method handlers for remote commands
   - Telemetry reporting for device status
   - Content synchronization from Azure Blob Storage

2. **MQTT Broker Integration**:
   - Real-time status updates via MQTT topics
   - Command handling via MQTT topics
   - Automatic reconnection with exponential backoff
   - Last Will and Testament for connection status

## Troubleshooting

### Common Issues

- **MPD Connection Errors**: Ensure MPD is running and accessible
- **Audio Device Issues**: Check audio device configuration and permissions
- **Docker Permission Problems**: Ensure proper device mapping and audio group access
- **Poetry Environment Issues**: Try recreating the virtual environment
- **MQTT Connection Issues**: Verify broker address and credentials
- **IoT Hub Connection Issues**: Check connection string and network connectivity

### Debugging Tools

- Use `waybox-player --debug` for verbose logging
- Check MPD logs for playback issues
- Use `aplay -l` to list available audio devices
- Run `docker logs waybox-player-python-dev` for container logs
- Use MQTT client tools like `mosquitto_sub` to monitor MQTT messages
- Use Azure CLI to monitor IoT Hub events
