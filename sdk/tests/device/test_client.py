"""
Tests for the IoTDeviceClient class.

This module tests the IoT device client which serves as a control layer for Azure IoT Hub
without direct interaction with the player module. The player interaction has been delegated
to the broker module.
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

# Import the test module
from tests.device.client_test_module import IoTDeviceClient
from tests.mocks.mock_azure import MockIoTHubDeviceClient, MockMessage, MockMethodRequest, MockMethodResponse

# Disable logging during tests
logging.disable(logging.CRITICAL)

# No need to patch as we're using the test module directly

class TestIoTDeviceClient(unittest.TestCase):
    """Tests for the IoTDeviceClient class."""

    def setUp(self):
        """Set up the test case."""
        # Create a mock player interface
        self.player_interface = MagicMock()

        # Set up default return values for player interface methods
        self.player_interface.play = MagicMock(return_value=True)
        self.player_interface.pause = MagicMock(return_value=True)
        self.player_interface.stop = MagicMock(return_value=True)
        self.player_interface.next = MagicMock(return_value=True)
        self.player_interface.previous = MagicMock(return_value=True)
        self.player_interface.set_volume = MagicMock(return_value=True)
        self.player_interface.get_status = MagicMock(return_value={"state": "playing", "volume": 80})
        self.player_interface.get_playlists = MagicMock(return_value=["Test Playlist 1", "Test Playlist 2"])
        self.player_interface.play_playlist = MagicMock(return_value=True)
        self.player_interface.set_repeat = MagicMock(return_value=True)
        self.player_interface.set_random = MagicMock(return_value=True)

        # Create the IoT client
        self.connection_string = "HostName=test-hub.azure-devices.net;DeviceId=test-device;SharedAccessKey=test-key"
        self.client = IoTDeviceClient(self.connection_string, self.player_interface)

        # Set up the event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down the test case."""
        self.loop.close()

    def test_init(self):
        """Test the initialization."""
        self.assertEqual(self.client.connection_string, self.connection_string)
        self.assertEqual(self.client.player, self.player_interface)
        self.assertFalse(self.client.connected)
        self.assertFalse(self.client.running)
        self.assertEqual(self.client.telemetry_interval, 60)

    def test_connect_and_disconnect(self):
        """Test the connect and disconnect methods."""
        # Test successful connection
        result = self.loop.run_until_complete(self.client.connect())
        self.assertTrue(result)
        self.assertTrue(self.client.connected)

        # Test disconnect
        self.loop.run_until_complete(self.client.disconnect())
        self.assertFalse(self.client.connected)

        # Reconnect for other tests
        self.loop.run_until_complete(self.client.connect())

    def test_start_stop(self):
        """Test the start and stop methods."""
        # Connect first
        self.loop.run_until_complete(self.client.connect())
        self.assertTrue(self.client.connected)

        # Test start
        self.loop.run_until_complete(self.client.start())
        self.assertTrue(self.client.running)

        # Test stop
        self.loop.run_until_complete(self.client.stop())
        self.assertFalse(self.client.running)

    def test_method_request_handler(self):
        """Test the method request handler."""
        # Connect first
        self.loop.run_until_complete(self.client.connect())

        # Test play method
        request = MockMethodRequest("play")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test pause method
        request = MockMethodRequest("pause")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test stop method
        request = MockMethodRequest("stop")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test next method
        request = MockMethodRequest("next")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test previous method
        request = MockMethodRequest("previous")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test setVolume method
        request = MockMethodRequest("setVolume", {"volume": 75})
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test getStatus method
        request = MockMethodRequest("getStatus")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])
        self.assertIn("status", response.payload)

        # Test getPlaylists method
        request = MockMethodRequest("getPlaylists")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])
        self.assertIn("playlists", response.payload)

        # Test playPlaylist method
        request = MockMethodRequest("playPlaylist", {"playlist": "Test Playlist 1"})
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test setRepeat method
        request = MockMethodRequest("setRepeat", {"repeat": True})
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test setRandom method
        request = MockMethodRequest("setRandom", {"random": True})
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 200)
        self.assertTrue(response.payload["result"])

        # Test unknown method
        request = MockMethodRequest("unknown")
        response = self.loop.run_until_complete(self.client._method_request_handler(request))
        self.assertEqual(response.status, 400)
        self.assertFalse(response.payload["result"])

    def test_desired_properties_handler(self):
        """Test the desired properties handler."""
        # Connect first
        self.loop.run_until_complete(self.client.connect())

        # Mock the twin manager's handle_desired_properties method
        original_handle = self.client.twin_manager.handle_desired_properties
        self.client.twin_manager.handle_desired_properties = AsyncMock()

        try:
            # Test desired properties handler
            patch = {"telemetry_interval": 30, "volume": 65}
            self.loop.run_until_complete(self.client._desired_properties_handler(patch))

            # Verify that the twin manager's handle_desired_properties was called
            self.client.twin_manager.handle_desired_properties.assert_called_once_with(patch)
        finally:
            # Restore the original method
            self.client.twin_manager.handle_desired_properties = original_handle

    def test_connection_state_change_handler(self):
        """Test the connection state change handler."""
        # Test connected state
        self.client._connection_state_change_handler(True)
        self.assertTrue(self.client.connected)

        # Test disconnected state
        self.client._connection_state_change_handler(False)
        self.assertFalse(self.client.connected)

    def test_send_message(self):
        """Test the send_message method."""
        # Connect first
        self.loop.run_until_complete(self.client.connect())

        # Test sending a message
        message = MockMessage("test")
        self.loop.run_until_complete(self.client.send_message(message))
        self.assertEqual(len(self.client.client.sent_messages), 1)
        self.assertEqual(self.client.client.sent_messages[0], message)

        # Test sending a message when disconnected
        self.client.connected = False
        with self.assertRaises(ConnectionError):
            self.loop.run_until_complete(self.client.send_message(message))

    def test_patch_twin_reported_properties(self):
        """Test the patch_twin_reported_properties method."""
        # Connect first
        self.loop.run_until_complete(self.client.connect())

        # Reset the reported properties
        self.client.client.reported_properties = {}

        # Test updating reported properties
        properties = {"test": "value"}
        self.loop.run_until_complete(self.client.patch_twin_reported_properties(properties))

        # Check that the properties were added to the reported properties
        self.assertIn("test", self.client.client.reported_properties)
        self.assertEqual(self.client.client.reported_properties["test"], "value")

        # Test updating reported properties when disconnected
        self.client.connected = False
        with self.assertRaises(ConnectionError):
            self.loop.run_until_complete(self.client.patch_twin_reported_properties(properties))

if __name__ == '__main__':
    unittest.main()
