#!/bin/bash
# Amora Testing Framework - Device Music Player Launcher
# This script starts the Amora device music player application

# Default configuration
MQTT_HOST="localhost"
MQTT_PORT=1883
DEVICE_ID="amora-test-device"
LOG_DIR="$(pwd)/tools/testing/logs"
CONFIG_DIR="$(pwd)/tools/testing/config/device"
VERBOSE=false
DEV_MODE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -b|--broker-host)
      MQTT_HOST="$2"
      shift 2
      ;;
    -p|--broker-port)
      MQTT_PORT="$2"
      shift 2
      ;;
    -d|--device-id)
      DEVICE_ID="$2"
      shift 2
      ;;
    -l|--log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    -c|--config-dir)
      CONFIG_DIR="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    --no-dev-mode)
      DEV_MODE=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -b, --broker-host HOST  MQTT broker hostname (default: localhost)"
      echo "  -p, --broker-port PORT  MQTT broker port (default: 1883)"
      echo "  -d, --device-id ID      Device ID (default: amora-test-device)"
      echo "  -l, --log-dir DIR       Log directory (default: ./tools/testing/logs)"
      echo "  -c, --config-dir DIR    Config directory (default: ./tools/testing/config/device)"
      echo "  -v, --verbose           Enable verbose output"
      echo "  --no-dev-mode           Disable development mode"
      echo "  -h, --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"

# Create device configuration file if it doesn't exist
DEVICE_CONFIG_FILE="$CONFIG_DIR/device_config.json"
if [ ! -f "$DEVICE_CONFIG_FILE" ]; then
  echo "Creating default device configuration file..."
  cat > "$DEVICE_CONFIG_FILE" << EOF
{
    "device": {
        "id": "$DEVICE_ID",
        "name": "Amora Test Device"
    },
    "mpd": {
        "host": "localhost",
        "port": 6600
    },
    "content": {
        "storage_path": "$(pwd)/edge/samples",
        "playlists_path": "$(pwd)/edge/samples/playlists"
    },
    "audio": {
        "backend": "pipewire",
        "device": "default",
        "volume": 80
    },
    "broker": {
        "broker_url": "$MQTT_HOST",
        "port": $MQTT_PORT,
        "use_tls": false,
        "reconnect_on_failure": true
    },
    "status_updater": {
        "enabled": true,
        "update_interval": 1.0,
        "position_update_interval": 1.0,
        "full_update_interval": 5.0
    },
    "dev_mode": $DEV_MODE
}
EOF
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed."
  exit 1
fi

# Function to handle script termination
cleanup() {
  echo "Stopping device music player..."
  if [ -f "$PLAYER_PID_FILE" ]; then
    PLAYER_PID=$(cat "$PLAYER_PID_FILE")
    kill "$PLAYER_PID" 2>/dev/null
    rm -f "$PLAYER_PID_FILE"
  fi
  echo "Device music player stopped."
  exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Set up logging
LOG_FILE="$LOG_DIR/device_player.log"
PLAYER_PID_FILE="$LOG_DIR/device_player.pid"

# Start the device music player
echo "Starting Amora device music player..."
echo "Device ID: $DEVICE_ID"
echo "MQTT Broker: $MQTT_HOST:$MQTT_PORT"
echo "Config file: $DEVICE_CONFIG_FILE"

# Set PYTHONPATH to include the SDK
export PYTHONPATH="$(pwd):$(pwd)/sdk:$PYTHONPATH"

# Run the music player application
if [ "$VERBOSE" = true ]; then
  python3 "$(pwd)/edge/music_player_app.py" --config "$DEVICE_CONFIG_FILE" 2>&1 | tee "$LOG_FILE" &
  PLAYER_PID=$!
else
  python3 "$(pwd)/edge/music_player_app.py" --config "$DEVICE_CONFIG_FILE" > "$LOG_FILE" 2>&1 &
  PLAYER_PID=$!
fi

echo $PLAYER_PID > "$PLAYER_PID_FILE"
echo "Device music player started with PID: $PLAYER_PID"
echo "Logs are being written to: $LOG_FILE"
echo "Press Ctrl+C to stop the player"

# Wait for the player process
wait $PLAYER_PID
