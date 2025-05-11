"""
IoT device client for AmoraSDK Device module.

This module provides the main IoT device client for connecting to Azure IoT Hub.
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, List, Optional, Callable

try:
    from azure.iot.device.aio import IoTHubDeviceClient as AzureIoTHubDeviceClient
    from azure.iot.device import Message, MethodResponse
    IOT_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Azure IoT Device SDK not available. IoT functionality will be disabled.")
    IOT_AVAILABLE = False
    # Define dummy classes for type hints
    class Message:
        """Dummy Message class for type hints."""
        pass

    class MethodResponse:
        """Dummy MethodResponse class for type hints."""
        pass

from .telemetry import TelemetryManager
from .twin import TwinManager

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

    async def connect(self) -> bool:
        """
        Connect to IoT Hub.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log connection string (with masked key for security)
            conn_str_parts = self.connection_string.split(';')
            masked_conn_str = []
            for part in conn_str_parts:
                if part.startswith('SharedAccessKey='):
                    key = part.split('=', 1)[1]
                    masked_key = key[:5] + '*****' + key[-5:] if len(key) > 10 else '*****'
                    masked_conn_str.append(f"SharedAccessKey={masked_key}")
                else:
                    masked_conn_str.append(part)
            logger.info(f"Connecting to IoT Hub with connection string: {';'.join(masked_conn_str)}")

            # Create client with custom MQTT settings
            self.client = AzureIoTHubDeviceClient.create_from_connection_string(
                self.connection_string,
                keep_alive=480  # MQTT keep-alive in seconds
            )

            # Register connection status callback
            self.client.on_connection_state_change = self._connection_state_change_handler

            # Connect to IoT Hub
            logger.info("Connecting to IoT Hub with custom MQTT settings")
            await self.client.connect()
            self.connected = True
            logger.info("Connected to IoT Hub")

            # Register direct method handlers
            self.client.on_method_request_received = self._method_request_handler

            # Register desired property change handler
            self.client.on_twin_desired_properties_patch_received = self._desired_properties_handler

            # Update reported properties with initial state
            await self.twin_manager.update_reported_properties()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to IoT Hub: {e}")
            logger.error(f"Connection string format error. Please check the format: HostName=<hub>.azure-devices.net;DeviceId=<device>;SharedAccessKey=<key>")
            return False

    async def disconnect(self):
        """Disconnect from IoT Hub."""
        if self.client:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from IoT Hub")

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

    async def send_message(self, message: Message):
        """
        Send a message to IoT Hub.

        Args:
            message (Message): Message to send
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

        logger.warning("Connection error detected, forcing reconnection")
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

        logger.info(f"Method request received: {method_name}, payload: {payload}")

        # Default response
        response_payload = {"result": False, "message": f"Method {method_name} not implemented"}
        status = 400

        # Process method request
        if method_name in self.method_handlers:
            try:
                result, response_payload, status = await self.method_handlers[method_name](payload)
            except Exception as e:
                logger.error(f"Error handling method {method_name}: {e}")
                response_payload = {"result": False, "message": f"Error: {str(e)}"}
                status = 500

        # Send response
        method_response = MethodResponse.create_from_method_request(
            method_request, status, response_payload
        )

        await self.client.send_method_response(method_response)
        logger.info(f"Method response sent: {response_payload}")

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
            logger.info("IoT Hub connection state changed: Connected")
            self.connected = True
            self.reconnect_attempts = 0

            # Log network information for debugging
            try:
                import socket
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                logger.info(f"Connected from host: {hostname}, IP: {ip_address}")
            except Exception as e:
                logger.warning(f"Could not get network information: {e}")
        else:
            # Disconnected
            logger.warning("IoT Hub connection state changed: Disconnected")
            self.connected = False

            # Start reconnection process if we're still running
            if self.running and not self.reconnect_task:
                self.reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        """Reconnect to IoT Hub with improved exponential backoff."""
        logger.info("Starting reconnection process")

        # Use a lock to prevent multiple reconnection attempts at the same time
        async with self.connection_lock:
            # If we're already connected, no need to reconnect
            if self.connected:
                logger.info("Already connected, skipping reconnection")
                self.reconnect_task = None
                return

            # Reset reconnect attempts if it's been a while since the last attempt
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.info("Resetting reconnection attempts counter")
                self.reconnect_attempts = 0

            while self.running and not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1

                # Calculate backoff time with exponential backoff and jitter
                backoff_time = min(
                    self.reconnect_interval * (self.reconnect_backoff_factor ** (self.reconnect_attempts - 1)),
                    self.max_backoff_time
                )
                jitter = backoff_time * 0.2 * random.random()
                wait_time = backoff_time + jitter

                logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)

                if not self.running:
                    logger.info("Client stopped during reconnection wait - aborting reconnect")
                    break

                try:
                    # Check if client needs to be recreated
                    if self.client is None:
                        logger.info("Client is None, recreating client")
                        self.client = AzureIoTHubDeviceClient.create_from_connection_string(
                            self.connection_string,
                            keep_alive=480
                        )

                    # Register connection status callback
                    self.client.on_connection_state_change = self._connection_state_change_handler

                    logger.info("Attempting to reconnect to IoT Hub")
                    await self.client.connect()
                    logger.info("Successfully reconnected to IoT Hub")
                    self.connected = True
                    self.reconnect_attempts = 0  # Reset counter on successful connection

                    # Re-register handlers (they might have been lost during disconnect)
                    self.client.on_method_request_received = self._method_request_handler
                    self.client.on_twin_desired_properties_patch_received = self._desired_properties_handler

                    # Update reported properties
                    await self.twin_manager.update_reported_properties()

                    break
                except Exception as e:
                    logger.error(f"Failed to reconnect to IoT Hub: {e}")

                    # If we've had multiple failures, try recreating the client
                    if self.reconnect_attempts > 3:
                        try:
                            logger.info("Multiple reconnection failures, recreating client")
                            if self.client:
                                await self.client.disconnect()
                            self.client = AzureIoTHubDeviceClient.create_from_connection_string(
                                self.connection_string,
                                keep_alive=480
                            )
                        except Exception as client_ex:
                            logger.error(f"Error recreating client: {client_ex}")

            if not self.connected and self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts")
                logger.info("Will try again later with reset counter")

            # Reset the reconnect task
            self.reconnect_task = None
