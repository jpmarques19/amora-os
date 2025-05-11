# Python Waybox Player

A Python-based audio player for Waybox with Pipewire backend and Azure IoT Hub integration.

## Features

- MPD-based audio playback
- Pipewire audio backend
- Playlist management
- Docker container support
- Azure IoT Hub integration for remote control and telemetry
- Automatic playback of commercial music files
- Stable IoT connection with improved reconnection logic

## Quick Start

To build and run the player in a single step:

```bash
./build_and_run.sh
```

This script will:
1. Stop and remove any existing container
2. Build a new container with all components
3. Start the container
4. Show the initial logs

## Container Details

The container includes:
- MPD music player daemon
- Python application for controlling the player
- Azure IoT Hub client for remote control and telemetry
- Sample commercial music files

## Manual Build and Run

If you prefer to build and run manually:

```bash
# Build the container
docker build -t waybox-player-python-dev-sdk -f Dockerfile.complete ..

# Run the container
docker run -d --name waybox-player-python-dev-sdk -p 5000:5000 waybox-player-python-dev-sdk
```

## Viewing Logs

To view the container logs:

```bash
docker logs -f waybox-player-python-dev-sdk
```

## Accessing the Container

To access the container shell:

```bash
docker exec -it waybox-player-python-dev-sdk bash
```

## Troubleshooting

If you encounter issues:

1. Check the container logs for error messages
2. Verify network connectivity to Azure IoT Hub
3. Ensure the sample music files are properly loaded

## Development

See the developer documentation for more details.
