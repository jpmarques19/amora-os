"""
Modified version of client.py for testing.

This module provides a test version of the IoT device client which serves as a control layer
for Azure IoT Hub without direct interaction with the player module. The player interaction
has been delegated to the broker module.
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, List, Optional, Callable
import sys
import os

# Add the device directory to the path
device_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../amora_sdk/device'))
sys.path.insert(0, device_path)

# Import directly
from iot import telemetry
from iot import twin
from iot.telemetry import TelemetryManager
from iot.twin import TwinManager

# Import mocks
from tests.mocks.mock_azure import MockIoTHubDeviceClient, MockMessage, MockMethodResponse

# Mock Azure IoT Hub Device Client
AzureIoTHubDeviceClient = MockIoTHubDeviceClient
Message = MockMessage
MethodResponse = MockMethodResponse
IOT_AVAILABLE = True

logger = logging.getLogger(__name__)

class IoTDeviceClient:
    """
    IoT Device Client for AmoraSDK.

    This client serves as a control layer for Azure IoT Hub for device management,
    diagnostics, and low-level operations. It does not directly interact with the
    player module as that functionality has been delegated to the broker module.
    """

    def __init__(self, connection_string: str, player_interface):
        """
        Initialize the IoT Device Client.

        Args:
            connection_string (str): Device connection string
            player_interface: Player interface instance
        """
        if not IOT_AVAILABLE:
            raise ImportError("Azure IoT Device SDK not available. Cannot create IoT client.")

        self.connection_string = connection_string
        self.player = player_interface
        self.client = None
        self.running = False
        self.telemetry_interval = 60  # seconds
        self.reconnect_interval = 10  # seconds
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        self.reconnect_task = None
        self.connected = False
        self.reconnect_backoff_factor = 1.5  # Exponential backoff factor
        self.max_backoff_time = 300  # Maximum backoff time in seconds (5 minutes)
        self.connection_lock = asyncio.Lock()  # Lock to prevent multiple reconnection attempts

        # Create telemetry and twin managers
        self.telemetry_manager = TelemetryManager(self, player_interface, self.telemetry_interval)
        self.twin_manager = TwinManager(self, player_interface)

        # Method handlers
        self.method_handlers = {
            "play": self._handle_play,
            "pause": self._handle_pause,
            "stop": self._handle_stop,
            "next": self._handle_next,
            "previous": self._handle_previous,
            "setVolume": self._handle_set_volume,
            "getStatus": self._handle_get_status,
            "getPlaylists": self._handle_get_playlists,
            "playPlaylist": self._handle_play_playlist,
            "setRepeat": self._handle_set_repeat,
            "setRandom": self._handle_set_random
        }

    async def connect(self) -> bool:
        """
        Connect to IoT Hub.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create client with custom MQTT settings
            self.client = AzureIoTHubDeviceClient.create_from_connection_string(
                self.connection_string,
                keep_alive=480  # MQTT keep-alive in seconds
            )

            # Register connection status callback
            self.client.on_connection_state_change = self._connection_state_change_handler

            # Connect to IoT Hub
            await self.client.connect()
            self.connected = True

            # Register direct method handlers
            self.client.on_method_request_received = self._method_request_handler

            # Register desired property change handler
            self.client.on_twin_desired_properties_patch_received = self._desired_properties_handler

            # Update reported properties with initial state
            await self.twin_manager.update_reported_properties()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to IoT Hub: {e}")
            return False

    async def disconnect(self):
        """Disconnect from IoT Hub."""
        if self.client:
            await self.client.disconnect()
            self.connected = False

    async def start(self):
        """Start the IoT client."""
        self.running = True

        # Start telemetry
        await self.telemetry_manager.start()

    async def stop(self):
        """Stop the IoT client."""
        self.running = False

        # Stop telemetry
        await self.telemetry_manager.stop()

        # Cancel any pending reconnect tasks
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass

        await self.disconnect()

    async def send_message(self, message):
        """
        Send a message to IoT Hub.

        Args:
            message: Message to send
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to IoT Hub")

        await self.client.send_message(message)

    async def patch_twin_reported_properties(self, reported_properties: Dict[str, Any]):
        """
        Update reported properties in device twin.

        Args:
            reported_properties (Dict[str, Any]): Reported properties to update
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to IoT Hub")

        await self.client.patch_twin_reported_properties(reported_properties)

    async def handle_connection_error(self):
        """Handle connection error."""
        if not self.connected:
            return

        self.connected = False

        if not self.reconnect_task:
            self.reconnect_task = asyncio.create_task(self._reconnect())

    async def _method_request_handler(self, method_request):
        """
        Handle direct method requests.

        Args:
            method_request: Method request object

        Returns:
            MethodResponse: Method response
        """
        method_name = method_request.name
        payload = method_request.payload

        # Default response
        response_payload = {"result": False, "message": f"Method {method_name} not implemented"}
        status = 400

        # Process method request
        if method_name in self.method_handlers:
            try:
                result, response_payload, status = await self.method_handlers[method_name](payload)
            except Exception as e:
                response_payload = {"result": False, "message": f"Error: {str(e)}"}
                status = 500

        # Send response
        method_response = MethodResponse.create_from_method_request(
            method_request, status, response_payload
        )

        await self.client.send_method_response(method_response)

        return method_response

    async def _desired_properties_handler(self, patch):
        """
        Handle desired property changes.

        Args:
            patch: Desired property patch
        """
        await self.twin_manager.handle_desired_properties(patch)

    def _connection_state_change_handler(self, status):
        """
        Handle connection state changes.

        Args:
            status: Connection status
        """
        if status:
            # Connected
            self.connected = True
            self.reconnect_attempts = 0
        else:
            # Disconnected
            self.connected = False

            # Start reconnection process if we're still running
            if self.running and not self.reconnect_task:
                self.reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        """Reconnect to IoT Hub."""
        # Simplified reconnect for testing
        try:
            await self.connect()
        except Exception:
            pass
        finally:
            self.reconnect_task = None

    # Method handlers

    async def _handle_play(self, payload):
        """Handle play method."""
        result = self.player.play()
        response_payload = {"result": result, "message": "Play command executed"}
        status = 200 if result else 500
        return result, response_payload, status

    async def _handle_pause(self, payload):
        """Handle pause method."""
        result = self.player.pause()
        response_payload = {"result": result, "message": "Pause command executed"}
        status = 200 if result else 500
        return result, response_payload, status

    async def _handle_stop(self, payload):
        """Handle stop method."""
        result = self.player.stop()
        response_payload = {"result": result, "message": "Stop command executed"}
        status = 200 if result else 500
        return result, response_payload, status

    async def _handle_next(self, payload):
        """Handle next method."""
        result = self.player.next()
        response_payload = {"result": result, "message": "Next command executed"}
        status = 200 if result else 500
        return result, response_payload, status

    async def _handle_previous(self, payload):
        """Handle previous method."""
        result = self.player.previous()
        response_payload = {"result": result, "message": "Previous command executed"}
        status = 200 if result else 500
        return result, response_payload, status

    async def _handle_set_volume(self, payload):
        """Handle setVolume method."""
        if isinstance(payload, dict) and "volume" in payload:
            volume = payload["volume"]
            result = self.player.set_volume(volume)
            response_payload = {"result": result, "message": f"Volume set to {volume}"}
            status = 200 if result else 500
        else:
            result = False
            response_payload = {"result": False, "message": "Invalid payload for setVolume method"}
            status = 400
        return result, response_payload, status

    async def _handle_get_status(self, payload):
        """Handle getStatus method."""
        status_data = self.player.get_status()
        response_payload = {"result": True, "status": status_data}
        status = 200
        return True, response_payload, status

    async def _handle_get_playlists(self, payload):
        """Handle getPlaylists method."""
        playlists = self.player.get_playlists()
        response_payload = {"result": True, "playlists": playlists}
        status = 200
        return True, response_payload, status

    async def _handle_play_playlist(self, payload):
        """Handle playPlaylist method."""
        if isinstance(payload, dict) and "playlist" in payload:
            playlist_name = payload["playlist"]
            result = self.player.play_playlist(playlist_name)
            response_payload = {"result": result, "message": f"Playing playlist {playlist_name}"}
            status = 200 if result else 500
        else:
            result = False
            response_payload = {"result": False, "message": "Invalid payload for playPlaylist method"}
            status = 400
        return result, response_payload, status

    async def _handle_set_repeat(self, payload):
        """Handle setRepeat method."""
        if isinstance(payload, dict) and "repeat" in payload:
            repeat = payload["repeat"]
            result = self.player.set_repeat(repeat)
            response_payload = {"result": result, "message": f"Repeat mode set to {repeat}"}
            status = 200 if result else 500
        else:
            result = False
            response_payload = {"result": False, "message": "Invalid payload for setRepeat method"}
            status = 400
        return result, response_payload, status

    async def _handle_set_random(self, payload):
        """Handle setRandom method."""
        if isinstance(payload, dict) and "random" in payload:
            random_mode = payload["random"]
            result = self.player.set_random(random_mode)
            response_payload = {"result": result, "message": f"Random mode set to {random_mode}"}
            status = 200 if result else 500
        else:
            result = False
            response_payload = {"result": False, "message": "Invalid payload for setRandom method"}
            status = 400
        return result, response_payload, status
