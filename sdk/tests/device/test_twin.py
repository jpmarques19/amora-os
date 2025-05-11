"""
Tests for the TwinManager class.
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
from iot.twin import TwinManager
from tests.mocks.mock_player import MockMusicPlayer

# Disable logging during tests
logging.disable(logging.CRITICAL)

# Patch the PlayerInterface
patch('interface.MusicPlayer', MockMusicPlayer).start()

class TestTwinManager(unittest.TestCase):
    """Tests for the TwinManager class."""

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
        self.client.telemetry_interval = 60
        self.client.patch_twin_reported_properties = AsyncMock()

        # Create the twin manager
        self.twin_manager = TwinManager(self.client, self.player_interface)

        # Set up the event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down the test case."""
        self.loop.close()

    def test_init(self):
        """Test the initialization."""
        self.assertEqual(self.twin_manager.client, self.client)
        self.assertEqual(self.twin_manager.player, self.player_interface)
        self.assertIn("volume", self.twin_manager.desired_property_handlers)
        self.assertIn("telemetry_interval", self.twin_manager.desired_property_handlers)
        self.assertIn("repeat", self.twin_manager.desired_property_handlers)
        self.assertIn("random", self.twin_manager.desired_property_handlers)

    def test_register_desired_property_handler(self):
        """Test the register_desired_property_handler method."""
        # Create a mock handler
        handler = AsyncMock()

        # Register the handler
        self.twin_manager.register_desired_property_handler("test", handler)

        # Check that the handler was registered
        self.assertIn("test", self.twin_manager.desired_property_handlers)
        self.assertEqual(self.twin_manager.desired_property_handlers["test"], handler)

    def test_handle_desired_properties(self):
        """Test the handle_desired_properties method."""
        # Create mock handlers
        volume_handler = AsyncMock()
        telemetry_handler = AsyncMock()

        # Register the handlers
        self.twin_manager.desired_property_handlers["volume"] = volume_handler
        self.twin_manager.desired_property_handlers["telemetry_interval"] = telemetry_handler

        # Create a patch
        patch = {
            "volume": 75,
            "telemetry_interval": 30
        }

        # Handle the patch
        self.loop.run_until_complete(self.twin_manager.handle_desired_properties(patch))

        # Check that the handlers were called
        volume_handler.assert_called_once_with(75)
        telemetry_handler.assert_called_once_with(30)

        # Check that update_reported_properties was called
        self.client.patch_twin_reported_properties.assert_called()

        # Test with a handler that raises an exception
        volume_handler.reset_mock()
        telemetry_handler.reset_mock()
        self.client.patch_twin_reported_properties.reset_mock()

        volume_handler.side_effect = Exception("Test exception")

        # Handle the patch
        self.loop.run_until_complete(self.twin_manager.handle_desired_properties(patch))

        # Check that the handlers were called
        volume_handler.assert_called_once_with(75)
        telemetry_handler.assert_called_once_with(30)

        # Check that update_reported_properties was called
        self.client.patch_twin_reported_properties.assert_called()

    def test_update_reported_properties(self):
        """Test the update_reported_properties method."""
        # Test with client connected
        self.loop.run_until_complete(self.twin_manager.update_reported_properties())

        # Check that patch_twin_reported_properties was called
        self.client.patch_twin_reported_properties.assert_called()

        # Test with client disconnected
        self.client.connected = False
        self.client.patch_twin_reported_properties.reset_mock()

        self.loop.run_until_complete(self.twin_manager.update_reported_properties())

        # Check that patch_twin_reported_properties was not called
        self.client.patch_twin_reported_properties.assert_not_called()

        # Test with patch_twin_reported_properties raising an exception
        self.client.connected = True
        self.client.patch_twin_reported_properties.side_effect = Exception("Test exception")

        self.loop.run_until_complete(self.twin_manager.update_reported_properties())

        # Should not raise an exception

    def test_handle_volume(self):
        """Test the _handle_volume method."""
        # Test setting volume
        self.loop.run_until_complete(self.twin_manager._handle_volume(75))

        # Check that the volume was set
        self.assertEqual(self.player_interface.get_volume(), 75)

    def test_handle_telemetry_interval(self):
        """Test the _handle_telemetry_interval method."""
        # Test setting telemetry interval
        self.loop.run_until_complete(self.twin_manager._handle_telemetry_interval(30))

        # Check that the telemetry interval was set
        self.assertEqual(self.client.telemetry_interval, 30)

    def test_handle_repeat(self):
        """Test the _handle_repeat method."""
        # Test setting repeat mode
        self.loop.run_until_complete(self.twin_manager._handle_repeat(True))

        # Check that repeat mode was set
        self.assertTrue(self.player_interface.player.repeat)

    def test_handle_random(self):
        """Test the _handle_random method."""
        # Test setting random mode
        self.loop.run_until_complete(self.twin_manager._handle_random(True))

        # Check that random mode was set
        self.assertTrue(self.player_interface.player.random)

if __name__ == '__main__':
    unittest.main()
