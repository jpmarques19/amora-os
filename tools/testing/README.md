# Amora Music System Testing Framework

This directory contains a comprehensive testing framework for the end-to-end Amora music system. The framework provides individual launch scripts that run in separate terminal windows to isolate and manage the different components of the system.

## Overview

The testing framework consists of the following components:

1. **MQTT Broker** - A local Mosquitto MQTT broker for real-time communication between the device and web player
2. **Device Music Player** - The Amora device music player application that connects to the MQTT broker
3. **Web Player UI Server** - A local web server that serves the Amora web player interface
4. **Master Launcher** - A script that can launch all components in sequence with proper startup delays

## Directory Structure

```
tools/testing/
├── README.md                 # This file
├── start_mqtt_broker.sh      # Script to start the MQTT broker
├── start_device_player.sh    # Script to start the device music player
├── start_web_player.sh       # Script to start the web player UI server
├── start_amora_system.sh     # Master script to launch all components
├── config/                   # Configuration files for the components
│   ├── device/               # Device configuration
│   └── mosquitto/            # Mosquitto configuration
└── logs/                     # Log files for all components
```

## Prerequisites

- **Mosquitto MQTT Broker** - Install using your package manager:
  - Ubuntu/Debian: `sudo apt-get install mosquitto`
  - Fedora/RHEL: `sudo dnf install mosquitto`
  - macOS: `brew install mosquitto`
- **Python 3** - Required for running the device player and web server
- **Bash** - The scripts are written in Bash

## Usage

### Starting the Entire System

To start all components of the Amora music system:

```bash
cd /path/to/amora-os
./tools/testing/start_amora_system.sh
```

This will launch all components in separate terminal windows with default settings.

### Command-line Options

The master script supports various command-line options:

```bash
./tools/testing/start_amora_system.sh --help
```

Common options include:

- `-b, --broker-host HOST` - MQTT broker hostname (default: localhost)
- `-p, --broker-port PORT` - MQTT broker port (default: 1883)
- `-w, --web-port PORT` - Web server port (default: 8080)
- `-d, --device-id ID` - Device ID (default: amora-test-device)
- `-v, --verbose` - Enable verbose output
- `--no-dev-mode` - Disable development mode
- `-s, --startup-delay SEC` - Delay between component startups (default: 2)

### Starting Individual Components

You can also start each component individually:

#### MQTT Broker

```bash
./tools/testing/start_mqtt_broker.sh
```

#### Device Music Player

```bash
./tools/testing/start_device_player.sh
```

#### Web Player UI Server

```bash
./tools/testing/start_web_player.sh
```

Each script supports its own set of command-line options. Use the `--help` option to see the available options for each script.

## Testing Workflow

1. Start the entire system using the master script
2. Open the web player UI in your browser at http://localhost:8080
3. Connect to the MQTT broker using the connection panel
4. Control the device music player using the web interface
5. Verify that commands are properly transmitted and executed
6. Check the logs in the `logs` directory for any errors or issues

## Customization

### Configuration Files

The testing framework creates default configuration files in the `config` directory. You can modify these files to customize the behavior of the components:

- `config/mosquitto/mosquitto.conf` - Mosquitto MQTT broker configuration
- `config/device/device_config.json` - Device music player configuration

### Log Files

All log files are stored in the `logs` directory:

- `logs/mosquitto.log` - MQTT broker logs
- `logs/device_player.log` - Device music player logs
- `logs/web_player.log` - Web player UI server logs
- `logs/amora_system.log` - Master launcher logs

## Troubleshooting

### MQTT Broker Issues

- Verify that Mosquitto is installed correctly
- Check the MQTT broker logs for any errors
- Ensure that the MQTT port (default: 1883) is not in use by another application

### Device Player Issues

- Verify that the Python environment is set up correctly
- Check the device player logs for any errors
- Ensure that the MQTT broker is running before starting the device player

### Web Player Issues

- Verify that the web player directory exists
- Check the web player logs for any errors
- Ensure that the web port (default: 8080) is not in use by another application

## Extending the Framework

To extend the testing framework:

1. Add new scripts to the `tools/testing` directory
2. Update the master script to include the new components
3. Add any necessary configuration files to the `config` directory
4. Update this README with information about the new components
