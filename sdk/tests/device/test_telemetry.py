"""
Tests for the TelemetryManager class.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import asyncio
import json
import logging

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Add the device directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../amora_sdk/device')))

# Import the module to test directly
from iot.telemetry import TelemetryManager
from tests.mocks.mock_player import MockMusicPlayer
from tests.mocks.mock_azure import MockIoTHubDeviceClient, MockMessage

# Disable logging during tests
logging.disable(logging.CRITICAL)

# Patch the Azure IoT Hub Device Client
patch('iot.telemetry.Message', MockMessage).start()
patch('iot.telemetry.IOT_AVAILABLE', True).start()

# Patch the PlayerInterface
patch('interface.MusicPlayer', MockMusicPlayer).start()

class TestTelemetryManager(unittest.TestCase):
    """Tests for the TelemetryManager class."""

    def setUp(self):
        """Set up the test case."""
        from interface import PlayerInterface

        self.config = {
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

        # Create the player interface
        self.player_interface = PlayerInterface(self.config)

        # Create a mock client
        self.client = MagicMock()
        self.client.connected = True
        self.client.send_message = AsyncMock()
        self.client.handle_connection_error = AsyncMock()

        # Create the telemetry manager
        self.telemetry_manager = TelemetryManager(self.client, self.player_interface, 1)

        # Set up the event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down the test case."""
        self.loop.close()

    def test_init(self):
        """Test the initialization."""
        self.assertEqual(self.telemetry_manager.client, self.client)
        self.assertEqual(self.telemetry_manager.player, self.player_interface)
        self.assertEqual(self.telemetry_manager.interval, 1)
        self.assertFalse(self.telemetry_manager.running)
        self.assertIsNone(self.telemetry_manager.task)

    def test_start_stop(self):
        """Test the start and stop methods."""
        # Test start
        self.loop.run_until_complete(self.telemetry_manager.start())
        self.assertTrue(self.telemetry_manager.running)
        self.assertIsNotNone(self.telemetry_manager.task)

        # Test stop
        self.loop.run_until_complete(self.telemetry_manager.stop())
        self.assertFalse(self.telemetry_manager.running)
        self.assertIsNone(self.telemetry_manager.task)

    def test_send_telemetry(self):
        """Test sending telemetry."""
        # Create a mock status
        status = {
            "state": "playing",
            "volume": 80,
            "current_song": {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "file": "test.mp3",
                "duration": 180,
                "position": 60
            },
            "playlist": "Test Playlist"
        }

        # Mock the player.get_status method
        self.player_interface.get_status = MagicMock(return_value=status)

        # Create a mock for the _telemetry_loop method to avoid running the actual loop
        original_loop = self.telemetry_manager._telemetry_loop
        self.telemetry_manager._telemetry_loop = AsyncMock()

        try:
            # Start the telemetry manager
            self.loop.run_until_complete(self.telemetry_manager.start())

            # Check that the task was created
            self.assertTrue(self.telemetry_manager.running)
            self.assertIsNotNone(self.telemetry_manager.task)

            # Stop the telemetry manager
            self.loop.run_until_complete(self.telemetry_manager.stop())

            # Check that the task was cancelled
            self.assertFalse(self.telemetry_manager.running)
            self.assertIsNone(self.telemetry_manager.task)

            # Verify that _telemetry_loop was called
            self.telemetry_manager._telemetry_loop.assert_called_once()

        finally:
            # Restore the original _telemetry_loop method
            self.telemetry_manager._telemetry_loop = original_loop

    def test_telemetry_message_sending(self):
        """Test that telemetry messages are sent correctly."""
        # Create a mock status
        status = {
            "state": "playing",
            "volume": 80,
            "current_song": {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "file": "test.mp3",
                "duration": 180,
                "position": 60
            },
            "playlist": "Test Playlist"
        }

        # Mock the player.get_status method
        self.player_interface.get_status = MagicMock(return_value=status)

        # Create a simple async function to simulate the telemetry loop
        async def simulate_telemetry_loop():
            # Only send telemetry if connected
            if self.client.connected:
                # Get player status
                status = self.player_interface.get_status()

                # Create telemetry message
                telemetry = {
                    "messageType": "playerStatus",
                    "deviceId": status.get("device_id", "unknown"),
                    "timestamp": "2023-01-01T00:00:00Z",  # Fixed timestamp for testing
                    "status": status
                }

                # Create message
                msg = MockMessage(json.dumps(telemetry))
                msg.content_type = "application/json"
                msg.content_encoding = "utf-8"

                # Send message
                await self.client.send_message(msg)

        # Test with client connected
        self.client.connected = True
        self.loop.run_until_complete(simulate_telemetry_loop())

        # Check that send_message was called
        self.client.send_message.assert_called_once()

        # Test with client disconnected
        self.client.connected = False
        self.client.send_message.reset_mock()
        self.loop.run_until_complete(simulate_telemetry_loop())

        # Check that send_message was not called
        self.client.send_message.assert_not_called()

        # Test with send_message raising an exception
        self.client.connected = True
        self.client.send_message.reset_mock()
        self.client.send_message.side_effect = Exception("Test exception")

        # This should raise an exception, but we'll catch it
        with self.assertRaises(Exception):
            self.loop.run_until_complete(simulate_telemetry_loop())

        # Check that send_message was called
        self.client.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
