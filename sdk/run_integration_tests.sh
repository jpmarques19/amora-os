#!/bin/bash
# Run the integration tests for the AmoraSDK

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if pytest is installed
if ! python -c "import pytest" &> /dev/null; then
    echo "Installing pytest..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Check if Azure IoT Device SDK is installed
if ! python -c "import azure.iot.device" &> /dev/null; then
    echo "Installing Azure IoT Device SDK..."
    pip install azure-iot-device
fi

# Check if python-mpd2 is installed
if ! python -c "import mpd" &> /dev/null; then
    echo "Installing python-mpd2..."
    pip install python-mpd2
fi

# Run the MPD integration tests
echo "Running MPD integration tests..."
python -m pytest integration_tests/device/player/ -v

# Check if Azure IoT Hub connection string is set in environment variable
if [ -z "$AMORA_IOT_HUB_CONNECTION_STRING" ]; then
    # Check if Azure IoT Hub connection string is set in config file
    CONFIG_FILE="integration_tests/config.json"
    if [ -f "$CONFIG_FILE" ]; then
        # Check if the config file contains a non-empty IoT Hub connection string
        IOT_HUB_CONNECTION_STRING=$(python -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); f.close(); print(config.get('azure', {}).get('iot_hub_connection_string', ''))")
        if [ -n "$IOT_HUB_CONNECTION_STRING" ]; then
            # Run the Azure IoT Hub integration tests
            echo "Running Azure IoT Hub integration tests (using connection string from config file)..."
            python -m pytest integration_tests/device/test_iot_client.py -v
            exit_code=$?
            if [ $exit_code -ne 0 ]; then
                exit $exit_code
            fi
        else
            echo "Skipping Azure IoT Hub integration tests (connection string not found in config file)"
        fi
    else
        echo "Skipping Azure IoT Hub integration tests (config file not found)"
    fi
else
    # Run the Azure IoT Hub integration tests
    echo "Running Azure IoT Hub integration tests (using connection string from environment variable)..."
    python -m pytest integration_tests/device/test_iot_client.py -v
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        exit $exit_code
    fi
fi

# Exit with the status of the last test
exit $?
