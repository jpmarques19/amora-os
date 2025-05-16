"""
Unit tests for the MQTT Test Server.

This module contains unit tests for the MQTT Test Server component.
"""

import unittest
import asyncio
import json
import sys
import os
import time
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the mock server module
from test_app.mqtt_test.tests.mock_server import MQTTTestServer
from test_app.mqtt_test.tests.mocks import MockMusicPlayer, MockBrokerManager

# Import the mock SDK modules
from test_app.mqtt_test.tests.mock_sdk import CommandMessage, ResponseMessage, StateMessage

class TestMQTTTestServer(unittest.TestCase):
    """Test cases for the MQTT Test Server."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test configurations
        self.mqtt_config = {
            "broker_url": "localhost",
            "port": 1883,
            "device_id": "amora-test-device",
            "topic_prefix": "amora/test",
            "use_tls": False
        }

        self.player_config = {
            "mpd_host": "localhost",
            "mpd_port": 6600,
            "storage_path": "/tmp/amora-test/music",
            "playlists_path": "/tmp/amora-test/playlists",
            "dev_mode": True
        }

        # Create server instance
        self.server = MQTTTestServer(self.mqtt_config, self.player_config)

        # Replace player and broker manager with mocks for testing
        self.mock_player = MockMusicPlayer(self.player_config)
        self.mock_broker_manager = MockBrokerManager(self.mqtt_config, self.mock_player)

        self.server.player = self.mock_player
        self.server.broker_manager = self.mock_broker_manager

        # Set up command handlers again with the mock broker manager
        self.server._setup_command_handlers()

        # Set up event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        # Close event loop
        self.loop.close()

    def test_init(self):
        """Test initialization."""
        # Check that the server was initialized correctly
        self.assertEqual(self.server.mqtt_config, self.mqtt_config)
        self.assertEqual(self.server.player_config, self.player_config)
        self.assertEqual(self.server.player, self.mock_player)
        self.assertEqual(self.server.broker_manager, self.mock_broker_manager)
        self.assertFalse(self.server.running)
        self.assertIsNone(self.server.status_update_task)

    def test_create_player(self):
        """Test player creation."""
        # Create a new server to test player creation
        server = MQTTTestServer(self.mqtt_config, self.player_config)

        # Get the player configuration
        player = server._create_player()

        # Check that the player was created with the correct configuration
        self.assertEqual(player.config["mpd"]["host"], self.player_config["mpd_host"])
        self.assertEqual(player.config["mpd"]["port"], self.player_config["mpd_port"])
        self.assertEqual(player.config["content"]["storage_path"], self.player_config["storage_path"])
        self.assertEqual(player.config["content"]["playlists_path"], self.player_config["playlists_path"])
        self.assertEqual(player.config["dev_mode"], self.player_config["dev_mode"])

    def test_create_broker_manager(self):
        """Test broker manager creation."""
        # Create a new server to test broker manager creation
        server = MQTTTestServer(self.mqtt_config, self.player_config)

        # Get the broker manager
        broker_manager = server._create_broker_manager()

        # Check that the broker manager was created with the correct configuration
        self.assertEqual(broker_manager.config.broker_url, self.mqtt_config["broker_url"])
        self.assertEqual(broker_manager.config.port, self.mqtt_config["port"])
        self.assertEqual(broker_manager.config.device_id, self.mqtt_config["device_id"])
        self.assertEqual(broker_manager.config.topic_prefix, self.mqtt_config["topic_prefix"])
        self.assertEqual(broker_manager.config.connection_options.use_tls, self.mqtt_config["use_tls"])

    def test_setup_command_handlers(self):
        """Test command handler setup."""
        # Check that command handlers were registered
        self.assertIn("play", self.mock_broker_manager.command_handlers)
        self.assertIn("pause", self.mock_broker_manager.command_handlers)
        self.assertIn("stop", self.mock_broker_manager.command_handlers)
        self.assertIn("next", self.mock_broker_manager.command_handlers)
        self.assertIn("previous", self.mock_broker_manager.command_handlers)
        self.assertIn("setVolume", self.mock_broker_manager.command_handlers)
        self.assertIn("getStatus", self.mock_broker_manager.command_handlers)
        self.assertIn("getPlaylists", self.mock_broker_manager.command_handlers)
        self.assertIn("playPlaylist", self.mock_broker_manager.command_handlers)

    def test_handle_play(self):
        """Test play command handler."""
        # Create a command message
        command = CommandMessage(
            command="play",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_play(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Play command executed")

        # Check that the player method was called
        self.assertIn(("play", []), self.mock_player.method_calls)

    def test_handle_pause(self):
        """Test pause command handler."""
        # Create a command message
        command = CommandMessage(
            command="pause",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_pause(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Pause command executed")

        # Check that the player method was called
        self.assertIn(("pause", []), self.mock_player.method_calls)

    def test_handle_stop(self):
        """Test stop command handler."""
        # Create a command message
        command = CommandMessage(
            command="stop",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_stop(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Stop command executed")

        # Check that the player method was called
        self.assertIn(("stop", []), self.mock_player.method_calls)

    def test_handle_next(self):
        """Test next command handler."""
        # Create a command message
        command = CommandMessage(
            command="next",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_next(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Next command executed")

        # Check that the player method was called
        self.assertIn(("next", []), self.mock_player.method_calls)

    def test_handle_previous(self):
        """Test previous command handler."""
        # Create a command message
        command = CommandMessage(
            command="previous",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_previous(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Previous command executed")

        # Check that the player method was called
        self.assertIn(("previous", []), self.mock_player.method_calls)

    def test_handle_set_volume(self):
        """Test setVolume command handler."""
        # Create a command message
        command = CommandMessage(
            command="setVolume",
            command_id="test-command-id",
            params={"volume": 75},
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_set_volume(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Volume set to 75")

        # Check that the player method was called
        self.assertIn(("set_volume", [75]), self.mock_player.method_calls)

    def test_handle_set_volume_default(self):
        """Test setVolume command handler with default volume."""
        # Create a command message with no volume parameter
        command = CommandMessage(
            command="setVolume",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_set_volume(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Volume set to 50")

        # Check that the player method was called with default volume
        self.assertIn(("set_volume", [50]), self.mock_player.method_calls)

    def test_handle_get_status(self):
        """Test getStatus command handler."""
        # Set up mock player status
        self.mock_player.status = {
            "state": "play",
            "volume": 75,
            "current_song": {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album"
            },
            "repeat": True,
            "random": False
        }

        # Create a command message
        command = CommandMessage(
            command="getStatus",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_get_status(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Status retrieved")
        self.assertEqual(response.data["status"], self.mock_player.status)

        # Check that the player method was called
        self.assertIn(("get_status", []), self.mock_player.method_calls)

    def test_handle_get_playlists(self):
        """Test getPlaylists command handler."""
        # Create a command message
        command = CommandMessage(
            command="getPlaylists",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_get_playlists(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Playlists retrieved")
        self.assertEqual(response.data["playlists"], ["playlist1", "playlist2", "playlist3"])

        # Check that the player method was called
        self.assertIn(("get_playlists", []), self.mock_player.method_calls)

    def test_handle_play_playlist(self):
        """Test playPlaylist command handler."""
        # Create a command message
        command = CommandMessage(
            command="playPlaylist",
            command_id="test-command-id",
            params={"playlist": "playlist1"},
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_play_playlist(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Playing playlist playlist1")

        # Check that the player method was called
        self.assertIn(("play_playlist", ["playlist1"]), self.mock_player.method_calls)

    def test_handle_play_playlist_no_playlist(self):
        """Test playPlaylist command handler with no playlist specified."""
        # Create a command message with no playlist parameter
        command = CommandMessage(
            command="playPlaylist",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Call the handler
        response = self.loop.run_until_complete(
            self.server._handle_play_playlist(command)
        )

        # Check the response
        self.assertEqual(response.command_id, command.command_id)
        self.assertFalse(response.result)
        self.assertEqual(response.message, "No playlist specified")

        # Check that the player method was not called
        self.assertNotIn(("play_playlist", [None]), self.mock_player.method_calls)

    def test_start(self):
        """Test server start method."""
        # Call the start method
        self.loop.run_until_complete(self.server.start())

        # Check that the player and broker were connected
        self.assertTrue(self.mock_player.connected)
        self.assertTrue(self.mock_broker_manager.connected)

        # Check that the server is running
        self.assertTrue(self.server.running)

        # Check that the status update task was created
        self.assertIsNotNone(self.server.status_update_task)

    @patch('test_app.mqtt_test.tests.mock_server.asyncio.create_task')
    def test_start_player_connect_failure(self, mock_create_task):
        """Test server start method with player connection failure."""
        # Set up mocks
        self.mock_player.connect = MagicMock(return_value=False)

        # Call the start method
        self.loop.run_until_complete(self.server.start())

        # Check that the server is not running
        self.assertFalse(self.server.running)

        # Check that the status update task was not created
        mock_create_task.assert_not_called()

    @patch('test_app.mqtt_test.tests.mock_server.asyncio.create_task')
    def test_start_broker_connect_failure(self, mock_create_task):
        """Test server start method with broker connection failure."""
        # Set up mocks
        self.mock_broker_manager.connect = MagicMock(return_value=False)

        # Call the start method
        self.loop.run_until_complete(self.server.start())

        # Check that the server is not running
        self.assertFalse(self.server.running)

        # Check that the status update task was not created
        mock_create_task.assert_not_called()

    def test_stop(self):
        """Test server stop method."""
        # Set up server state
        self.server.running = True

        # Create a mock task that can be awaited
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        mock_task.__await__ = lambda self: (yield from asyncio.sleep(0).__await__())

        self.server.status_update_task = mock_task

        # Call the stop method
        self.loop.run_until_complete(self.server.stop())

        # Check that the server is not running
        self.assertFalse(self.server.running)

        # Check that the status update task was cancelled
        self.server.status_update_task.cancel.assert_called_once()

        # Check that the player and broker were disconnected
        self.assertFalse(self.mock_player.connected)
        self.assertFalse(self.mock_broker_manager.connected)

    @patch('test_app.mqtt_test.tests.mock_sdk.StateMessage.from_player_state')
    def test_update_status(self, mock_from_player_state):
        """Test status update method."""
        # Set up mocks
        mock_state_message = MagicMock()
        mock_from_player_state.return_value = mock_state_message

        # Set up server state
        self.server.running = True

        # Create a task for the update_status method
        task = asyncio.ensure_future(self.server._update_status(), loop=self.loop)

        # Run the event loop for a bit
        self.loop.run_until_complete(asyncio.sleep(0.1))

        # Stop the server
        self.server.running = False

        # Run the event loop until the task completes
        self.loop.run_until_complete(task)

        # Check that the player status was retrieved
        self.assertIn(("get_status", []), self.mock_player.method_calls)

        # Check that the state message was created and published
        mock_from_player_state.assert_called_with(self.mock_player.status)
        self.assertIn(("state", mock_state_message), self.mock_broker_manager.published_messages)

if __name__ == "__main__":
    unittest.main()
