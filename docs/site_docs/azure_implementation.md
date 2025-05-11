# AmoraSDK Azure Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the AmoraSDK using Azure IoT Hub and Event Hub for device control and real-time status synchronization.

## Prerequisites

- Azure subscription
- Azure CLI installed
- Python 3.9 or later
- Node.js 14 or later (for client SDK)

## Implementation Steps

### 1. Set Up Azure Resources

#### Create Resource Group

```bash
# Create a resource group
az group create --name rg-amora-os --location westeurope
```

#### Create IoT Hub

```bash
# Create an IoT Hub
az iot hub create --name amora-iot-hub --resource-group rg-amora-os --sku S1
```

#### Create Event Hub

```bash
# Create an Event Hub namespace
az eventhubs namespace create --name amora-event-hub-ns --resource-group rg-amora-os --location westeurope

# Create an Event Hub
az eventhubs eventhub create --name amora-status-events --resource-group rg-amora-os --namespace-name amora-event-hub-ns --message-retention 1
```

#### Create IoT Hub Routing to Event Hub

```bash
# Get Event Hub connection string
eventHubConnectionString=$(az eventhubs namespace authorization-rule keys list --resource-group rg-amora-os --namespace-name amora-event-hub-ns --name RootManageSharedAccessKey --query primaryConnectionString -o tsv)

# Create a routing endpoint
az iot hub routing-endpoint create --hub-name amora-iot-hub --resource-group rg-amora-os --endpoint-name EventHubEndpoint --endpoint-type eventhub --endpoint-resource-group rg-amora-os --endpoint-subscription-id $(az account show --query id -o tsv) --connection-string $eventHubConnectionString

# Create a route
az iot hub route create --hub-name amora-iot-hub --resource-group rg-amora-os --endpoint-name EventHubEndpoint --source DeviceMessages --route-name StatusRoute --condition "true"
```

#### Register a Device

```bash
# Register a device
az iot hub device-identity create --hub-name amora-iot-hub --device-id amora-player-001

# Get the device connection string
deviceConnectionString=$(az iot hub device-identity connection-string show --hub-name amora-iot-hub --device-id amora-player-001 --query connectionString -o tsv)
```

### 2. Implement Device-Side SDK

#### Install Azure IoT Device SDK

```bash
# Using Poetry
poetry add azure-iot-device

# Or using pip
pip install azure-iot-device
```

#### Create IoT Device Client

Create a file `sdk/amora_sdk/iot_client.py`:

```python
"""
IoT client for AmoraSDK.
"""

import json
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, MethodResponse

logger = logging.getLogger(__name__)

class IoTDeviceClient:
    """IoT Device Client for AmoraSDK."""

    def __init__(self, connection_string: str, player_interface):
        """
        Initialize the IoT Device Client.

        Args:
            connection_string (str): Device connection string
            player_interface: Player interface instance
        """
        self.connection_string = connection_string
        self.player = player_interface
        self.client = None
        self.running = False
        self.telemetry_interval = 1  # seconds

    async def connect(self) -> bool:
        """
        Connect to IoT Hub.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create client
            self.client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)

            # Connect to IoT Hub
            await self.client.connect()
            logger.info("Connected to IoT Hub")

            # Register direct method handlers
            self.client.on_method_request_received = self._method_request_handler

            # Register desired property change handler
            self.client.on_twin_desired_properties_patch_received = self._desired_properties_handler

            # Update reported properties with initial state
            await self._update_reported_properties()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to IoT Hub: {e}")
            return False

    async def disconnect(self):
        """Disconnect from IoT Hub."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from IoT Hub")

    async def start(self):
        """Start the IoT client."""
        self.running = True

        # Start telemetry loop
        asyncio.create_task(self._telemetry_loop())

    async def stop(self):
        """Stop the IoT client."""
        self.running = False
        await self.disconnect()

    async def _telemetry_loop(self):
        """Send telemetry periodically."""
        while self.running:
            try:
                # Get player status
                status = self.player.get_status()

                # Create telemetry message
                telemetry = {
                    "messageType": "playerStatus",
                    "deviceId": self.client.device_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": status
                }

                # Send telemetry
                message = Message(json.dumps(telemetry))
                message.content_type = "application/json"
                message.content_encoding = "utf-8"
                await self.client.send_message(message)

                # Update reported properties periodically
                await self._update_reported_properties()

                # Wait for next interval
                await asyncio.sleep(self.telemetry_interval)
            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")
                await asyncio.sleep(self.telemetry_interval)

    async def _update_reported_properties(self):
        """Update reported properties in device twin."""
        try:
            # Get player status
            status = self.player.get_status()

            # Get playlists
            playlists = self.player.get_playlists()

            # Create reported properties
            reported_properties = {
                "status": status,
                "playlists": playlists,
                "lastUpdated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

            # Update reported properties
            await self.client.patch_twin_reported_properties(reported_properties)
        except Exception as e:
            logger.error(f"Error updating reported properties: {e}")

    async def _method_request_handler(self, method_request):
        """
        Handle direct method requests.

        Args:
            method_request: Method request object
        """
        # Default response
        response_payload = {"result": False, "message": "Unknown method"}
        status = 400

        try:
            # Process method request
            if method_request.name == "play":
                result = self.player.play()
                response_payload = {"result": result, "message": "Playback started" if result else "Failed to start playback"}
                status = 200 if result else 500

            elif method_request.name == "pause":
                result = self.player.pause()
                response_payload = {"result": result, "message": "Playback paused" if result else "Failed to pause playback"}
                status = 200 if result else 500

            elif method_request.name == "stop":
                result = self.player.stop()
                response_payload = {"result": result, "message": "Playback stopped" if result else "Failed to stop playback"}
                status = 200 if result else 500

            elif method_request.name == "next":
                result = self.player.next()
                response_payload = {"result": result, "message": "Skipped to next track" if result else "Failed to skip to next track"}
                status = 200 if result else 500

            elif method_request.name == "previous":
                result = self.player.previous()
                response_payload = {"result": result, "message": "Skipped to previous track" if result else "Failed to skip to previous track"}
                status = 200 if result else 500

            elif method_request.name == "setVolume":
                payload = json.loads(method_request.payload)
                volume = payload.get("volume", 50)
                result = self.player.set_volume(volume)
                response_payload = {"result": result, "message": f"Volume set to {volume}" if result else "Failed to set volume"}
                status = 200 if result else 500

            elif method_request.name == "getPlaylists":
                playlists = self.player.get_playlists()
                response_payload = {"result": True, "playlists": playlists}
                status = 200

            # Update reported properties after command execution
            await self._update_reported_properties()

        except Exception as e:
            logger.error(f"Error handling method request: {e}")
            response_payload = {"result": False, "message": str(e)}
            status = 500

        # Send response
        method_response = MethodResponse.create_from_method_request(method_request, status, response_payload)
        await self.client.send_method_response(method_response)

    async def _desired_properties_handler(self, desired_properties):
        """
        Handle desired property changes.

        Args:
            desired_properties: Desired properties patch
        """
        try:
            logger.info(f"Received desired properties: {desired_properties}")

            # Process command if present
            if "command" in desired_properties:
                command = desired_properties["command"]
                action = command.get("action")
                parameters = command.get("parameters", {})

                if action == "play":
                    self.player.play()
                elif action == "pause":
                    self.player.pause()
                elif action == "stop":
                    self.player.stop()
                elif action == "next":
                    self.player.next()
                elif action == "previous":
                    self.player.previous()
                elif action == "setVolume":
                    volume = parameters.get("volume", 50)
                    self.player.set_volume(volume)

            # Update reported properties after processing desired properties
            await self._update_reported_properties()

        except Exception as e:
            logger.error(f"Error handling desired properties: {e}")
```

#### Create Main SDK Module

Create a file `sdk/amora_sdk/__init__.py`:

```python
"""
AmoraSDK - SDK for controlling AmoraOS player device using Azure IoT Hub.
"""

from .iot_client import IoTDeviceClient
from .player_interface import PlayerInterface

__version__ = "0.1.0"
__all__ = ["IoTDeviceClient", "PlayerInterface"]
```

#### Create Player Interface

Create a file `sdk/amora_sdk/player_interface.py` (similar to the previous implementation but without WebSocket/HTTP API dependencies).

### 3. Implement Client-Side SDK

#### Install Azure IoT Service SDK

```bash
# Using npm
npm install azure-iothub azure-iot-device-mqtt @azure/event-hubs
```

#### Create Client SDK

Create a file `sdk/client/src/index.ts`:

```typescript
/**
 * AmoraSDK client using Azure IoT Hub.
 */

import { Client as IoTHubClient, Twin } from 'azure-iothub';
import { EventHubConsumerClient } from '@azure/event-hubs';
import { PlayerStatus, StatusUpdateCallback, ConnectionStatusCallback, CommandResponse } from './types';

export { PlayerStatus, StatusUpdateCallback, ConnectionStatusCallback, CommandResponse };

/**
 * AmoraSDK client.
 */
export class AmoraClient {
  private iotHubClient: IoTHubClient;
  private eventHubClient: EventHubConsumerClient;
  private deviceId: string;
  private statusCallbacks: StatusUpdateCallback[] = [];
  private connectionCallbacks: ConnectionStatusCallback[] = [];
  private connected = false;
  private consumerGroup = '$Default';

  /**
   * Create a new AmoraSDK client.
   *
   * @param iotHubConnectionString IoT Hub connection string
   * @param eventHubConnectionString Event Hub connection string
   * @param deviceId Device ID
   */
  constructor(
    iotHubConnectionString: string,
    eventHubConnectionString: string,
    deviceId: string
  ) {
    this.iotHubClient = IoTHubClient.fromConnectionString(iotHubConnectionString);
    this.eventHubClient = new EventHubConsumerClient(
      this.consumerGroup,
      eventHubConnectionString
    );
    this.deviceId = deviceId;
  }

  /**
   * Connect to IoT Hub and Event Hub.
   */
  async connect(): Promise<void> {
    try {
      // Start receiving events
      this.eventHubClient.subscribe({
        processEvents: async (events, context) => {
          for (const event of events) {
            try {
              // Check if this is a status update for our device
              if (
                event.body &&
                event.body.messageType === 'playerStatus' &&
                event.body.deviceId === this.deviceId
              ) {
                const status = event.body.status as PlayerStatus;
                this.notifyStatusUpdate(status);
              }
            } catch (err) {
              console.error('Error processing event:', err);
            }
          }
        },
        processError: async (err, context) => {
          console.error('Error from Event Hub:', err);
          this.notifyConnectionStatus(false);
        }
      });

      this.connected = true;
      this.notifyConnectionStatus(true);
    } catch (err) {
      console.error('Failed to connect:', err);
      this.connected = false;
      this.notifyConnectionStatus(false);
      throw err;
    }
  }

  /**
   * Disconnect from IoT Hub and Event Hub.
   */
  async disconnect(): Promise<void> {
    try {
      await this.eventHubClient.close();
      this.connected = false;
      this.notifyConnectionStatus(false);
    } catch (err) {
      console.error('Error disconnecting:', err);
      throw err;
    }
  }

  /**
   * Register a callback for status updates.
   *
   * @param callback Callback function
   */
  onStatusUpdate(callback: StatusUpdateCallback): void {
    this.statusCallbacks.push(callback);
  }

  /**
   * Register a callback for connection status changes.
   *
   * @param callback Callback function
   */
  onConnectionStatus(callback: ConnectionStatusCallback): void {
    this.connectionCallbacks.push(callback);

    // Immediately notify of current status
    callback(this.connected);
  }

  /**
   * Remove a status update callback.
   *
   * @param callback Callback function to remove
   */
  removeStatusUpdateCallback(callback: StatusUpdateCallback): void {
    this.statusCallbacks = this.statusCallbacks.filter(cb => cb !== callback);
  }

  /**
   * Remove a connection status callback.
   *
   * @param callback Callback function to remove
   */
  removeConnectionStatusCallback(callback: ConnectionStatusCallback): void {
    this.connectionCallbacks = this.connectionCallbacks.filter(cb => cb !== callback);
  }

  /**
   * Get player status from device twin.
   *
   * @returns Player status
   */
  async getStatus(): Promise<PlayerStatus> {
    try {
      const twin = await this.getTwin();
      return twin.properties.reported.status;
    } catch (err) {
      console.error('Failed to get status:', err);
      return {
        state: 'unknown',
        volume: 0,
        current_song: null,
        playlist: null,
      };
    }
  }

  /**
   * Get available playlists from device twin.
   *
   * @returns List of available playlists
   */
  async getPlaylists(): Promise<string[]> {
    try {
      const twin = await this.getTwin();
      return twin.properties.reported.playlists || [];
    } catch (err) {
      console.error('Failed to get playlists:', err);
      return [];
    }
  }

  /**
   * Start or resume playback.
   *
   * @returns Command response
   */
  async play(): Promise<CommandResponse> {
    return this.invokeMethod('play');
  }

  /**
   * Pause playback.
   *
   * @returns Command response
   */
  async pause(): Promise<CommandResponse> {
    return this.invokeMethod('pause');
  }

  /**
   * Stop playback.
   *
   * @returns Command response
   */
  async stop(): Promise<CommandResponse> {
    return this.invokeMethod('stop');
  }

  /**
   * Skip to next track.
   *
   * @returns Command response
   */
  async next(): Promise<CommandResponse> {
    return this.invokeMethod('next');
  }

  /**
   * Skip to previous track.
   *
   * @returns Command response
   */
  async previous(): Promise<CommandResponse> {
    return this.invokeMethod('previous');
  }

  /**
   * Set volume level.
   *
   * @param volume Volume level (0-100)
   * @returns Command response
   */
  async setVolume(volume: number): Promise<CommandResponse> {
    return this.invokeMethod('setVolume', { volume });
  }

  /**
   * Invoke a direct method on the device.
   *
   * @param methodName Method name
   * @param payload Method payload
   * @returns Command response
   */
  private async invokeMethod(methodName: string, payload: any = {}): Promise<CommandResponse> {
    try {
      const methodParams = {
        methodName,
        payload,
        responseTimeoutInSeconds: 30,
        connectTimeoutInSeconds: 30,
      };

      const result = await this.iotHubClient.invokeDeviceMethod(this.deviceId, methodParams);

      return {
        success: result.result.result,
        message: result.result.message,
      };
    } catch (err) {
      console.error(`Failed to invoke method ${methodName}:`, err);
      return {
        success: false,
        message: `Failed to invoke method ${methodName}: ${err}`,
      };
    }
  }

  /**
   * Get device twin.
   *
   * @returns Device twin
   */
  private async getTwin(): Promise<Twin> {
    return new Promise((resolve, reject) => {
      this.iotHubClient.getTwin(this.deviceId, (err, twin) => {
        if (err) {
          reject(err);
        } else {
          resolve(twin);
        }
      });
    });
  }

  /**
   * Notify all registered callbacks of a status update.
   *
   * @param status Player status
   */
  private notifyStatusUpdate(status: PlayerStatus): void {
    this.statusCallbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('Error in status update callback:', error);
      }
    });
  }

  /**
   * Notify all registered callbacks of a connection status change.
   *
   * @param connected Connection status
   */
  private notifyConnectionStatus(connected: boolean): void {
    this.connectionCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('Error in connection status callback:', error);
      }
    });
  }
}
```

### 4. Update Device-Side Integration

#### Create Main Entry Point

Create a file `sdk/amora_sdk/__main__.py`:

```python
"""
Main entry point for AmoraSDK.
"""

import asyncio
import logging
import sys
import os
import argparse

from .iot_client import IoTDeviceClient
from .player_interface import PlayerInterface

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for AmoraSDK."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Parse arguments
    parser = argparse.ArgumentParser(description="AmoraSDK IoT Client")
    parser.add_argument("--connection-string", help="Device connection string")
    args = parser.parse_args()

    # Get connection string from arguments or environment variable
    connection_string = args.connection_string or os.environ.get("AMORA_DEVICE_CONNECTION_STRING")

    if not connection_string:
        logger.error("Device connection string not provided")
        return 1

    # Default configuration
    config = {
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
        "dev_mode": True
    }

    # Create player interface
    player = PlayerInterface(config)

    # Connect to player
    if not player.connect():
        logger.error("Failed to connect to player")
        return 1

    # Create IoT client
    iot_client = IoTDeviceClient(connection_string, player)

    # Connect to IoT Hub
    if not await iot_client.connect():
        logger.error("Failed to connect to IoT Hub")
        player.disconnect()
        return 1

    # Start IoT client
    await iot_client.start()

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        # Clean up
        await iot_client.stop()
        player.disconnect()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

#### Update pyproject.toml

Update `sdk/pyproject.toml`:

```toml
[tool.poetry]
name = "amora-sdk"
version = "0.1.0"
description = "SDK for controlling AmoraOS player device using Azure IoT Hub"
authors = ["AmoraOS Team"]
readme = "readme.md"
packages = [{include = "amora_sdk"}]

[tool.poetry.dependencies]
python = "^3.9"
azure-iot-device = "^2.12.0"
python-mpd2 = "^3.0.5"
pydantic = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.3.1"
pytest-cov = "^4.1.0"
black = "^23.3.0"
isort = "^5.12.0"
flake8 = "^6.0.0"
mypy = "^1.3.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry.scripts]
amora-iot-client = "amora_sdk.__main__:main"

[tool.black]
line-length = 88
target-version = ["py39"]

[tool.isort]
profile = "black"
line_length = 88
```

### 5. Update Dockerfile

Update `edge/Dockerfile` to include the SDK and Azure IoT dependencies:

```dockerfile
# Add to edge/Dockerfile

# Install Azure IoT dependencies
RUN pip install azure-iot-device

# Copy SDK files
COPY --chown=user:user sdk/amora_sdk /home/user/sdk/amora_sdk
```

### 6. Create Startup Script

Create a file `edge/scripts/start-iot-client.sh`:

```bash
#!/bin/bash
cd /home/user/app
source /home/user/venv/bin/activate
export PYTHONPATH=/home/user/app:/home/user/sdk
export AMORA_DEVICE_CONNECTION_STRING="YOUR_DEVICE_CONNECTION_STRING"
python -m amora_sdk
```

Update `edge/scripts/start.sh` to launch the IoT client:

```bash
# Add at the end of the file
echo "Starting IoT client..."
/home/user/app/scripts/start-iot-client.sh &
```
