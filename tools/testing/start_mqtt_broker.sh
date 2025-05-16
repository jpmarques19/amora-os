#!/bin/bash
# Amora Testing Framework - MQTT Broker Launcher
# This script starts a local Mosquitto MQTT broker for testing purposes

# Default configuration
MQTT_PORT=1883
MQTT_CONFIG_DIR="$(pwd)/tools/testing/config/mosquitto"
MQTT_LOG_DIR="$(pwd)/tools/testing/logs"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--port)
      MQTT_PORT="$2"
      shift 2
      ;;
    -c|--config-dir)
      MQTT_CONFIG_DIR="$2"
      shift 2
      ;;
    -l|--log-dir)
      MQTT_LOG_DIR="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -p, --port PORT        MQTT broker port (default: 1883)"
      echo "  -c, --config-dir DIR   Mosquitto config directory (default: ./tools/testing/config/mosquitto)"
      echo "  -l, --log-dir DIR      Log directory (default: ./tools/testing/logs)"
      echo "  -v, --verbose          Enable verbose output"
      echo "  -h, --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create necessary directories
mkdir -p "$MQTT_CONFIG_DIR"
mkdir -p "$MQTT_LOG_DIR"

# Create Mosquitto configuration file if it doesn't exist
MQTT_CONFIG_FILE="$MQTT_CONFIG_DIR/mosquitto.conf"
if [ ! -f "$MQTT_CONFIG_FILE" ]; then
  echo "Creating default Mosquitto configuration file..."
  cat > "$MQTT_CONFIG_FILE" << EOF
# Mosquitto MQTT Broker Configuration for Amora Testing
listener $MQTT_PORT
allow_anonymous true
persistence false
log_dest file $MQTT_LOG_DIR/mosquitto.log
log_type all
connection_messages true
EOF
fi

# Check if Mosquitto is installed
if ! command -v mosquitto &> /dev/null; then
  echo "Error: Mosquitto MQTT broker is not installed."
  echo "Please install it using your package manager:"
  echo "  Ubuntu/Debian: sudo apt-get install mosquitto"
  echo "  Fedora/RHEL: sudo dnf install mosquitto"
  echo "  macOS: brew install mosquitto"
  exit 1
fi

# Function to handle script termination
cleanup() {
  echo "Stopping MQTT broker..."
  if [ -f "$MQTT_PID_FILE" ]; then
    MQTT_PID=$(cat "$MQTT_PID_FILE")
    kill "$MQTT_PID" 2>/dev/null
    rm -f "$MQTT_PID_FILE"
  else
    # Try to find and kill the mosquitto process
    pkill -f "mosquitto -c $MQTT_CONFIG_FILE" 2>/dev/null
  fi
  echo "MQTT broker stopped."
  exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Start Mosquitto MQTT broker
echo "Starting MQTT broker on port $MQTT_PORT..."
MQTT_PID_FILE="$MQTT_LOG_DIR/mosquitto.pid"

if [ "$VERBOSE" = true ]; then
  mosquitto -c "$MQTT_CONFIG_FILE" -v &
  MQTT_PID=$!
  echo $MQTT_PID > "$MQTT_PID_FILE"
  echo "MQTT broker started with PID: $MQTT_PID (verbose mode)"
else
  mosquitto -c "$MQTT_CONFIG_FILE" -d
  if [ $? -eq 0 ]; then
    echo "MQTT broker started in background mode"
    # Wait a moment for the broker to start
    sleep 1
    # Check if the broker is running
    if pgrep -f "mosquitto -c $MQTT_CONFIG_FILE" > /dev/null; then
      echo "MQTT broker is running successfully"
    else
      echo "Error: MQTT broker failed to start"
      exit 1
    fi
  else
    echo "Error: Failed to start MQTT broker"
    exit 1
  fi
fi

# Display connection information
echo "MQTT broker is running on localhost:$MQTT_PORT"
echo "Press Ctrl+C to stop the broker"

# Keep the script running in foreground mode
if [ "$VERBOSE" = true ]; then
  # If in verbose mode, wait for the mosquitto process
  wait $MQTT_PID
else
  # Otherwise, just keep the script running
  while true; do
    sleep 1
    # Check if mosquitto is still running
    if ! pgrep -f "mosquitto -c $MQTT_CONFIG_FILE" > /dev/null; then
      echo "MQTT broker has stopped unexpectedly"
      exit 1
    fi
  done
fi
