# AmoraOS - Intelligent Edge Audio Platform with SDK

A Python implementation of an edge device audio system that provides a custom SDK for seamless integration with Waybox applications. This project migrates from Arch Linux to Debian Bookworm on Raspberry Pi music boxes, enabling sophisticated edge audio capabilities with cloud connectivity.

> **Note:** IoT integration is currently a work in progress. The roadmap includes full Azure IoT Hub integration for device management and the AmoraSDK development for seamless integration with Waybox applications.

## Features

- Python-based edge audio player with MPD and MPC for control and playback
- Azure IoT Hub integration for remote device management and monitoring
- Cloud-based content synchronization and device orchestration
- python-mpd2 library for MPD client functionality
- Pipewire audio backend for modern audio routing
- Playlist management and playback control
- Development mode for testing on Windows host
- Poetry for dependency management
- Comprehensive test suite with high coverage
- Containerized deployment with Debian Bookworm
- Support for IQUADIO PI DA audio HAT

## Architecture

<img src="docs/images/amora-os-overview.jpeg" alt="AmoraOS Architecture" width="800"/>

The application follows a modular architecture with containerized components on edge devices connecting to Azure IoT Hub:

- **Edge Device**: Raspberry Pi running Debian Bookworm with containerized components
- **Python App**: Main application logic handling device-side operations
- **Music Player Daemon**: Handles audio playback and playlist management
- **Azure IoT SDK**: Manages cloud connectivity, device twins, and commands
- **Raspberry Pi & IQAUDIO DAC**: Hardware platform for high-quality audio at the edge

The containerized edge application communicates with Azure IoT Hub for device management, telemetry, and command processing, while using Azure Blob Storage for content synchronization.

- **Main Module**: Entry point with CLI interface using Click
- **Player Module**: Core functionality for MPD control and playback
- **Utils Module**: Audio device detection and configuration utilities
- **IoT Client**: Handles device-to-cloud and cloud-to-device messaging
- **Content Manager**: Synchronizes audio content from cloud storage
- **Configuration**: JSON-based configuration with Pydantic models

## Project Structure (WIP)

```
AmoraOS/
├── src/                # Core application code
│   ├── main.py         # Entry point and CLI
│   ├── player.py       # Player implementation
│   └── utils.py        # Utility functions
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── docs/               # Documentation
├── tests/              # Test suite
├── samples/            # Sample music for testing
├── Dockerfile          # Container definition
└── pyproject.toml      # Poetry project definition
```

## Development

### Setup with Poetry

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run the player
poetry run waybox-player start

# Run in development mode
poetry run waybox-player start --dev

# Test audio
poetry run waybox-player test-audio

# Run tests with coverage
poetry run pytest --cov=src
```

### Windows Development

For Windows development, a PowerShell script is provided:

```powershell
# Interactive menu mode
.\dev.ps1

# Or use direct command-line parameters:
.\dev.ps1 -Start    # Start container in dev mode
.\dev.ps1 -Test     # Run tests locally with coverage
.\dev.ps1 -Build    # Build container image
.\dev.ps1 -Clean    # Clean up containers
```

#### Logging System

The dev.ps1 script includes an automatic logging system:

- All operations are logged to the `logs` directory
- Each run creates a timestamped log file (e.g., `waybox_dev_20250504_181523.log`)
- Only the last 3 log files are kept to prevent clutter
- The script exits after each operation completes
- To run another operation, start the script again

## Docker

### Container Setup

The application uses a Docker container setup:

- Based on Debian Bookworm
- Uses a Python virtual environment with pip for dependency management
- Mounts the samples directory for music files in development mode
- Uses volume mounts for source code, configuration, and scripts in development mode
- Includes MPD, Pipewire, and other required system packages

### Build the Docker Image

```bash
docker build -t waybox-python-player .
```

Or use the dev.ps1 script (option 3).

### Run in Normal Mode

```bash
docker run -d --name waybox-player-python --privileged --network host \
  -v ./music:/home/user/music \
  --device /dev/snd:/dev/snd \
  --group-add audio \
  waybox-python-player
```

### Run in Development Mode (Audio to Windows Host)

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

Note: The `samples` directory is mounted as `/home/user/music` in the container for development.

### Dependency Management

- Poetry is used for development on the host machine
- In the Docker container, we use a Python virtual environment with pip
- This approach provides a good balance between development experience and container stability
- When you add or update dependencies:
  1. Add them to pyproject.toml with Poetry:
     ```bash
     poetry add package-name
     ```
  2. Update the Dockerfile to include the new dependency in the pip install command
  3. Rebuild the container to apply the changes

Note: We use a virtual environment in the container because Debian Bookworm implements PEP 668, which prevents installing packages directly with pip into the system Python.

## Configuration

The application uses JSON configuration files:

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

## Audio Testing

To test audio functionality:

```bash
# Using the CLI
poetry run waybox-player test-audio

# Or directly with Python
python -m src.main test-audio
```

## Example Usage

See `scripts/example.py` for a complete example of how to use the player in your code:

```python
from player import MusicPlayer

# Create configuration
config = {
    "mpd": {"host": "localhost", "port": 6600},
    "content": {
        "storage_path": "/home/user/music",
        "playlists_path": "/home/user/music/playlists"
    },
    "audio": {"backend": "pipewire", "device": "default", "volume": 80}
}

# Create player instance
player = MusicPlayer(config)

# Connect to MPD
player.connect()

# Play audio
player.play()
```

## Sample Music Files

The project includes a `samples` directory for testing audio playback in development mode:

- Add MP3 files to the `samples` directory to test playback
- Create playlists by adding files to `samples/playlists/[playlist_name]`
- The `samples` directory is mounted as `/home/user/music` in the container
- For real testing, replace the placeholder text files with actual MP3 files

When running in development mode with the dev.ps1 script:
1. The script automatically mounts your local `samples` directory to `/home/user/music` in the container
2. It ensures proper permissions are set on the mounted directory
3. It updates the MPD database to recognize your music files
4. You can immediately play your music files using the player

### Testing Audio Playback

To quickly test audio playback with your sample MP3 files:

1. Start the container in dev mode using the dev.ps1 script (option 1)
2. When the bash shell opens in the container, run:
   ```bash
   /home/user/app/scripts/play-sample.sh
   ```
3. This script will:
   - Update the MPD database
   - List all available MP3 files
   - Add them to the playlist
   - Start playback
   - Show the current status

## Known Issues

- Some test cases related to keyboard interrupts and signal handling may fail
- Audio device detection may require manual configuration on some systems
- Development mode requires proper audio routing configuration

## Future Enhancements

- Complete Azure IoT Hub integration for edge device management
- Real-time device monitoring and diagnostics via IoT cloud
- Content synchronization from Azure Blob Storage 
- Over-the-air updates for AmoraOS on edge devices
- Fleet management capabilities for multiple edge devices
- Edge-to-cloud telemetry for performance monitoring
- Offline operation with cloud synchronization when available
- Enhanced security features for edge devices
