# AmoraSDK Integration Tests

This directory contains integration tests for the AmoraSDK. These tests interact with real services and dependencies, unlike unit tests which use mocks.

## Prerequisites

- Python 3.8 or higher
- MPD server running locally or remotely
- Azure IoT Hub (optional, for IoT tests)
- Azure Event Hub (optional, for IoT tests)

## Configuration

Integration tests can be configured in several ways:

1. **Environment Variables**:
   - `AMORA_MPD_HOST`: MPD server host (default: localhost)
   - `AMORA_MPD_PORT`: MPD server port (default: 6600)
   - `AMORA_CONTENT_STORAGE_PATH`: Path to store music files (default: /tmp/amora_test/music)
   - `AMORA_CONTENT_PLAYLISTS_PATH`: Path to store playlists (default: /tmp/amora_test/playlists)
   - `AMORA_IOT_HUB_CONNECTION_STRING`: Azure IoT Hub connection string
   - `AMORA_EVENT_HUB_CONNECTION_STRING`: Azure Event Hub connection string

2. **Local Configuration File**:
   - The file `integration_tests/config.json` contains the default configuration for non-sensitive settings.
   - This file is included in the repository and should not contain sensitive information like connection strings.

3. **User Configuration File**:
   - Create a file at `~/.amora/integration_test_config.json` for sensitive settings like connection strings.
   - This file is not included in the repository and is specific to your local environment.
   - Example structure:
   ```json
   {
     "azure": {
       "iot_hub_connection_string": "your_connection_string",
       "event_hub_connection_string": "your_connection_string"
     }
   }
   ```

4. **Configuration Helper Script**:
   - Use the `setup_config.py` script to easily set up your configuration:
   ```bash
   # Show current configuration
   ./setup_config.py show

   # Set up Azure configuration
   ./setup_config.py azure --iot-hub "your_iot_hub_connection_string" --event-hub "your_event_hub_connection_string"

   # Set up MPD configuration
   ./setup_config.py mpd --host "localhost" --port 6600

   # Set up content configuration
   ./setup_config.py content --storage-path "/tmp/amora_test/music" --playlists-path "/tmp/amora_test/playlists"
   ```

The configuration is loaded in the following order (later sources override earlier ones):
1. Default configuration (hardcoded)
2. Local config file (integration_tests/config.json)
3. User config file (~/.amora/integration_test_config.json)
4. Environment variables

## Running the Tests

### Using the Script

The easiest way to run the integration tests is to use the provided script:

```bash
./run_integration_tests.sh
```

This script will:
1. Activate the virtual environment if it exists
2. Install required dependencies if needed
3. Run the MPD integration tests
4. Run the Azure IoT Hub integration tests if the connection string is set

### Using pytest Directly

You can also run the tests directly using pytest:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all integration tests
python -m pytest integration_tests/

# Run only MPD integration tests
python -m pytest integration_tests/device/player/

# Run only IoT integration tests
python -m pytest integration_tests/device/test_iot_client.py
```

## Test Categories

### MPD Tests

These tests interact with a real MPD server to test the player functionality:

- `test_music_player.py`: Tests the MusicPlayer class
- `test_mpd_client.py`: Tests the MPDClientWrapper class

### Azure IoT Tests

These tests interact with Azure IoT Hub to test the IoT device client:

- `test_iot_client.py`: Tests the IoTDeviceClient class

## Skipping Tests

Tests will be automatically skipped if the required services are not available:

- MPD tests will be skipped if MPD is not running
- Azure IoT tests will be skipped if the connection string is not set

## Troubleshooting

### MPD Connection Issues

If you're having trouble connecting to MPD, check that:
- MPD is running (`systemctl status mpd`)
- MPD is listening on the expected host and port
- The firewall allows connections to the MPD port

### Azure IoT Hub Connection Issues

If you're having trouble connecting to Azure IoT Hub, check that:
- The connection string is correct
- The device exists in the IoT Hub
- The device has the correct permissions
