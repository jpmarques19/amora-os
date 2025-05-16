#!/bin/bash
# Amora Testing Framework - Master Launcher
# This script starts all components of the Amora music system for end-to-end testing

# Default configuration
MQTT_HOST="localhost"
MQTT_PORT=1883
WEB_PORT=8080
DEVICE_ID="amora-test-device"
LOG_DIR="$(pwd)/tools/testing/logs"
CONFIG_DIR="$(pwd)/tools/testing/config"
VERBOSE=false
DEV_MODE=true
STARTUP_DELAY=2

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
    -w|--web-port)
      WEB_PORT="$2"
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
    -s|--startup-delay)
      STARTUP_DELAY="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -b, --broker-host HOST  MQTT broker hostname (default: localhost)"
      echo "  -p, --broker-port PORT  MQTT broker port (default: 1883)"
      echo "  -w, --web-port PORT     Web server port (default: 8080)"
      echo "  -d, --device-id ID      Device ID (default: amora-test-device)"
      echo "  -l, --log-dir DIR       Log directory (default: ./tools/testing/logs)"
      echo "  -c, --config-dir DIR    Config directory (default: ./tools/testing/config)"
      echo "  -v, --verbose           Enable verbose output"
      echo "  --no-dev-mode           Disable development mode"
      echo "  -s, --startup-delay SEC Delay between component startups (default: 2)"
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

# Check if the script directory exists
SCRIPT_DIR="$(pwd)/tools/testing"
if [ ! -d "$SCRIPT_DIR" ]; then
  echo "Error: Script directory not found: $SCRIPT_DIR"
  exit 1
fi

# Check if the component scripts exist
MQTT_SCRIPT="$SCRIPT_DIR/start_mqtt_broker.sh"
DEVICE_SCRIPT="$SCRIPT_DIR/start_device_player.sh"
WEB_SCRIPT="$SCRIPT_DIR/start_web_player.sh"

for script in "$MQTT_SCRIPT" "$DEVICE_SCRIPT" "$WEB_SCRIPT"; do
  if [ ! -f "$script" ]; then
    echo "Error: Script not found: $script"
    exit 1
  fi
  # Make sure the script is executable
  chmod +x "$script"
done

# Function to handle script termination
cleanup() {
  echo "Stopping all components..."
  
  # Kill all child processes
  pkill -P $$
  
  echo "All components stopped."
  exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Create a master log file
MASTER_LOG="$LOG_DIR/amora_system.log"
echo "Starting Amora Music System - $(date)" > "$MASTER_LOG"
echo "Configuration:" >> "$MASTER_LOG"
echo "  MQTT Broker: $MQTT_HOST:$MQTT_PORT" >> "$MASTER_LOG"
echo "  Web Server: http://localhost:$WEB_PORT" >> "$MASTER_LOG"
echo "  Device ID: $DEVICE_ID" >> "$MASTER_LOG"
echo "  Development Mode: $DEV_MODE" >> "$MASTER_LOG"
echo "  Verbose Mode: $VERBOSE" >> "$MASTER_LOG"
echo "  Log Directory: $LOG_DIR" >> "$MASTER_LOG"
echo "  Config Directory: $CONFIG_DIR" >> "$MASTER_LOG"
echo "  Startup Delay: $STARTUP_DELAY seconds" >> "$MASTER_LOG"
echo "" >> "$MASTER_LOG"

# Display welcome message
echo "========================================================"
echo "  Amora Music System Testing Framework"
echo "========================================================"
echo "Starting all components with the following configuration:"
echo "  MQTT Broker: $MQTT_HOST:$MQTT_PORT"
echo "  Web Server: http://localhost:$WEB_PORT"
echo "  Device ID: $DEVICE_ID"
echo "  Development Mode: $DEV_MODE"
echo "  Verbose Mode: $VERBOSE"
echo "  Log Directory: $LOG_DIR"
echo "  Config Directory: $CONFIG_DIR"
echo "  Startup Delay: $STARTUP_DELAY seconds"
echo ""

# Start MQTT broker in a new terminal window
echo "Starting MQTT broker..."
if [ "$(uname)" == "Darwin" ]; then
  # macOS
  osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && $MQTT_SCRIPT -p $MQTT_PORT -l $LOG_DIR -c $CONFIG_DIR/mosquitto $([ "$VERBOSE" = true ] && echo "-v")\""
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  # Linux
  if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "$MQTT_SCRIPT -p $MQTT_PORT -l $LOG_DIR -c $CONFIG_DIR/mosquitto $([ "$VERBOSE" = true ] && echo "-v"); exec bash"
  elif command -v xterm &> /dev/null; then
    xterm -e "$MQTT_SCRIPT -p $MQTT_PORT -l $LOG_DIR -c $CONFIG_DIR/mosquitto $([ "$VERBOSE" = true ] && echo "-v")" &
  else
    echo "Warning: Could not find a suitable terminal emulator. Starting MQTT broker in background."
    $MQTT_SCRIPT -p $MQTT_PORT -l $LOG_DIR -c $CONFIG_DIR/mosquitto $([ "$VERBOSE" = true ] && echo "-v") &
  fi
else
  # Unsupported OS
  echo "Warning: Unsupported OS. Starting MQTT broker in background."
  $MQTT_SCRIPT -p $MQTT_PORT -l $LOG_DIR -c $CONFIG_DIR/mosquitto $([ "$VERBOSE" = true ] && echo "-v") &
fi

echo "Waiting for MQTT broker to start..."
sleep $STARTUP_DELAY

# Start device player in a new terminal window
echo "Starting device music player..."
if [ "$(uname)" == "Darwin" ]; then
  # macOS
  osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && $DEVICE_SCRIPT -b $MQTT_HOST -p $MQTT_PORT -d $DEVICE_ID -l $LOG_DIR -c $CONFIG_DIR/device $([ "$VERBOSE" = true ] && echo "-v") $([ "$DEV_MODE" = false ] && echo "--no-dev-mode")\""
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  # Linux
  if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "$DEVICE_SCRIPT -b $MQTT_HOST -p $MQTT_PORT -d $DEVICE_ID -l $LOG_DIR -c $CONFIG_DIR/device $([ "$VERBOSE" = true ] && echo "-v") $([ "$DEV_MODE" = false ] && echo "--no-dev-mode"); exec bash"
  elif command -v xterm &> /dev/null; then
    xterm -e "$DEVICE_SCRIPT -b $MQTT_HOST -p $MQTT_PORT -d $DEVICE_ID -l $LOG_DIR -c $CONFIG_DIR/device $([ "$VERBOSE" = true ] && echo "-v") $([ "$DEV_MODE" = false ] && echo "--no-dev-mode")" &
  else
    echo "Warning: Could not find a suitable terminal emulator. Starting device player in background."
    $DEVICE_SCRIPT -b $MQTT_HOST -p $MQTT_PORT -d $DEVICE_ID -l $LOG_DIR -c $CONFIG_DIR/device $([ "$VERBOSE" = true ] && echo "-v") $([ "$DEV_MODE" = false ] && echo "--no-dev-mode") &
  fi
else
  # Unsupported OS
  echo "Warning: Unsupported OS. Starting device player in background."
  $DEVICE_SCRIPT -b $MQTT_HOST -p $MQTT_PORT -d $DEVICE_ID -l $LOG_DIR -c $CONFIG_DIR/device $([ "$VERBOSE" = true ] && echo "-v") $([ "$DEV_MODE" = false ] && echo "--no-dev-mode") &
fi

echo "Waiting for device player to start..."
sleep $STARTUP_DELAY

# Start web player in a new terminal window
echo "Starting web player UI server..."
if [ "$(uname)" == "Darwin" ]; then
  # macOS
  osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && $WEB_SCRIPT -p $WEB_PORT -b $MQTT_HOST -q $MQTT_PORT -i $DEVICE_ID -l $LOG_DIR $([ "$VERBOSE" = true ] && echo "-v")\""
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  # Linux
  if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "$WEB_SCRIPT -p $WEB_PORT -b $MQTT_HOST -q $MQTT_PORT -i $DEVICE_ID -l $LOG_DIR $([ "$VERBOSE" = true ] && echo "-v"); exec bash"
  elif command -v xterm &> /dev/null; then
    xterm -e "$WEB_SCRIPT -p $WEB_PORT -b $MQTT_HOST -q $MQTT_PORT -i $DEVICE_ID -l $LOG_DIR $([ "$VERBOSE" = true ] && echo "-v")" &
  else
    echo "Warning: Could not find a suitable terminal emulator. Starting web player in background."
    $WEB_SCRIPT -p $WEB_PORT -b $MQTT_HOST -q $MQTT_PORT -i $DEVICE_ID -l $LOG_DIR $([ "$VERBOSE" = true ] && echo "-v") &
  fi
else
  # Unsupported OS
  echo "Warning: Unsupported OS. Starting web player in background."
  $WEB_SCRIPT -p $WEB_PORT -b $MQTT_HOST -q $MQTT_PORT -i $DEVICE_ID -l $LOG_DIR $([ "$VERBOSE" = true ] && echo "-v") &
fi

echo "All components started successfully!"
echo "Web player UI is available at: http://localhost:$WEB_PORT"
echo "Press Ctrl+C to stop all components"

# Keep the script running
while true; do
  sleep 1
done
