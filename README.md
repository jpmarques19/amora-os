# Python Waybox Player with Pipewire

A Python implementation of the Waybox audio player using Pipewire as the audio backend. This project is part of the Arch Linux to Fedora CoreOS migration effort for Raspberry Pi music boxes.

## Features

- Python-based audio player with MPD and MPC for control and playback
- python-mpd2 library for MPD client functionality
- Pipewire audio backend for modern audio routing
- Playlist management and playback control
- Development mode for testing on Windows host
- Poetry for dependency management
- Comprehensive test suite with high coverage
- Containerized deployment with Debian Bookworm
- Support for IQUADIO PI DA audio HAT

## Architecture

The application follows a modular architecture:

- **Main Module**: Entry point with CLI interface using Click
- **Player Module**: Core functionality for MPD control and playback
- **Utils Module**: Audio device detection and configuration utilities
- **Configuration**: JSON-based configuration with Pydantic models

## Project Structure

```
python-waybox-pipewire/
├── src/                    # Source code
│   ├── main.py             # Main entry point and CLI
│   ├── player.py           # MPD player implementation
│   └── utils.py            # Utility functions
├── config/                 # Configuration files
│   ├── config.json         # Default configuration
│   ├── config.dev.json     # Development configuration
│   └── mpd.conf            # MPD configuration
├── scripts/                # Utility scripts
│   ├── start.sh            # Container startup script
│   ├── test-audio.py       # Audio testing script
│   └── example.py          # Example usage script
├── samples/                # Sample music files for testing
│   ├── playlists/          # Sample playlists
│   └── README.md           # Information about sample files
├── tests/                  # Test suite
│   ├── test_main.py        # Tests for main module
│   ├── test_player.py      # Tests for player module
│   └── test_utils.py       # Tests for utils module
├── Dockerfile              # Container definition
├── pyproject.toml          # Poetry project definition
└── dev.ps1                 # PowerShell development script
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

- Azure IoT Hub integration for remote management
- Content synchronization from cloud storage
- Automatic updates for container images
- Enhanced monitoring and diagnostics
