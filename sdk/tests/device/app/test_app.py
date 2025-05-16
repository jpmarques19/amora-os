"""
Tests for the AmoraApp class.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
import json
import logging
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the MPD client
sys.modules['mpd'] = MagicMock()
sys.modules['mpd'].MPDClient = MagicMock

# Mock the MQTT client
sys.modules['paho'] = MagicMock()
sys.modules['paho.mqtt'] = MagicMock()
sys.modules['paho.mqtt.client'] = MagicMock()

# Import the modules
from amora_sdk.device.app.app import AmoraApp
from amora_sdk.device.broker.config import BrokerConfig, ConnectionOptions, QoS
from amora_sdk.device.broker.messages import CommandMessage, ResponseMessage

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestAmoraApp(unittest.TestCase):
    """Tests for the AmoraApp class."""

    def setUp(self):
        """Set up the test."""
        # Create a mock player interface
        self.mock_player = MagicMock()
        self.mock_player.get_status.return_value = {
            'state': 'play',
            'current_song': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'position': 30,
                'duration': 180,
                'file': 'test.mp3'
            },
            'volume': 80,
            'repeat': False,
            'random': False,
            'playlist': 'Test Playlist',
            'playlist_tracks': [{'title': 'Test Song', 'file': 'test.mp3'}]
        }
        self.mock_player.connect.return_value = True
        self.mock_player.disconnect.return_value = True

        # Create a mock broker manager
        self.mock_broker = MagicMock()
        self.mock_broker.connect.return_value = True
        self.mock_broker.disconnect.return_value = None
        self.mock_broker.publish_state.return_value = True

        # Create a config
        self.config = {
            "status_updater": {
                "enabled": True,
                "update_interval": 0.1,
                "position_update_interval": 0.1,
                "full_update_interval": 0.5
            }
        }

        # Create a broker config
        self.broker_config = BrokerConfig(
            broker_url="test.broker.com",
            port=1883,
            client_id="test_client",
            device_id="test_device",
            topic_prefix="amora/devices",
            connection_options=ConnectionOptions(
                use_tls=False,
                username="test_user",
                password="test_password"
            ),
            default_qos=QoS.AT_LEAST_ONCE,
            raw_config=self.config
        )

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_init(self, mock_broker_manager_class):
        """Test initialization."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Check that the broker manager was created with the correct parameters
        mock_broker_manager_class.assert_called_once_with(self.broker_config)

        # Check that the command callback was registered
        mock_broker_manager.register_command_callback.assert_called_once()

        # Check that the configuration was set correctly
        self.assertEqual(app.update_interval, 0.1)
        self.assertEqual(app.position_update_interval, 0.1)
        self.assertEqual(app.full_update_interval, 0.5)
        self.assertTrue(app.enable_status_updates)

        # Check that the status update state was initialized correctly
        self.assertFalse(app.running)
        self.assertIsNone(app.update_thread)
        self.assertIsNone(app.last_status)

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_connect(self, mock_broker_manager_class):
        """Test connect method."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager
        mock_broker_manager.connect.return_value = True

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Patch the start_status_updates method
        with patch.object(app, 'start_status_updates') as mock_start_status_updates:
            # Connect to services
            result = app.connect()

            # Check that the connection was successful
            self.assertTrue(result)

            # Check that the broker manager's connect method was called
            mock_broker_manager.connect.assert_called_once()

            # Check that the start_status_updates method was called
            mock_start_status_updates.assert_called_once()

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_disconnect(self, mock_broker_manager_class):
        """Test disconnect method."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Patch the stop_status_updates method
        with patch.object(app, 'stop_status_updates') as mock_stop_status_updates:
            # Disconnect from services
            app.disconnect()

            # Check that the stop_status_updates method was called
            mock_stop_status_updates.assert_called_once()

            # Check that the broker manager's disconnect method was called
            mock_broker_manager.disconnect.assert_called_once()

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_start_stop_status_updates(self, mock_broker_manager_class):
        """Test start_status_updates and stop_status_updates methods."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Start status updates
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            result = app.start_status_updates()

            # Check that the result is True
            self.assertTrue(result)

            # Check that the thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

            # Check that the running flag was set
            self.assertTrue(app.running)

            # Stop status updates
            app.stop_status_updates()

            # Check that the running flag was cleared
            self.assertFalse(app.running)

            # Check that the thread was joined
            mock_thread_instance.join.assert_called_once()

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_update_player_state(self, mock_broker_manager_class):
        """Test _update_player_state method."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager
        mock_broker_manager.publish_state.return_value = True

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Update player state
        result = app._update_player_state()

        # Check that the result is True
        self.assertTrue(result)

        # Check that the player's get_status method was called
        self.mock_player.get_status.assert_called_once()

        # Check that the broker manager's publish_state method was called with the correct parameters
        mock_broker_manager.publish_state.assert_called_once_with(self.mock_player.get_status.return_value)

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_command_handler(self, mock_broker_manager_class):
        """Test command handler."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Create a command message
        command_msg = CommandMessage(
            command="play",
            command_id="test_id",
            params={"playlist": "Test Playlist"}
        )

        # Get the command handler
        handler = app._create_command_handler("play")

        # Configure the player mock
        self.mock_player.play.return_value = True

        # Call the handler
        response = handler(command_msg)

        # Check that the player's play method was called with the correct parameters
        self.mock_player.play.assert_called_once_with(playlist="Test Playlist")

        # Check that the response is correct
        self.assertEqual(response.command_id, "test_id")
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Command play executed")
        self.assertEqual(response.data, {"result": True})

        # Check that the _update_player_state method was called
        with patch.object(app, '_update_player_state') as mock_update_player_state:
            # Call the handler again
            handler(command_msg)

            # Check that the _update_player_state method was called
            mock_update_player_state.assert_called_once()

    @patch('amora_sdk.device.app.app.BrokerManager')
    def test_check_and_update_status(self, mock_broker_manager_class):
        """Test _check_and_update_status method."""
        # Configure the mock
        mock_broker_manager = MagicMock()
        mock_broker_manager_class.return_value = mock_broker_manager

        # Create the app
        app = AmoraApp(self.mock_player, self.broker_config, self.config)

        # Set up the initial state
        app.last_status = {
            'state': 'play',
            'current_song': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'position': 30,
                'duration': 180,
                'file': 'test.mp3'
            },
            'volume': 80,
            'repeat': False,
            'random': False
        }
        app.last_full_update_time = time.time()
        app.last_position_update_time = time.time()

        # Test position update
        app.last_position_update_time = 0  # Force a position update

        # Configure the player mock to return a position update
        self.mock_player.get_status.return_value = {
            'state': 'play',
            'current_song': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'position': 31,
                'duration': 180,
                'file': 'test.mp3'
            },
            'volume': 80,
            'repeat': False,
            'random': False
        }

        # Check and update status
        app._check_and_update_status()

        # Check that the broker manager's publish_state method was called with the correct parameters
        mock_broker_manager.publish_state.assert_called_once()
        args, kwargs = mock_broker_manager.publish_state.call_args
        self.assertEqual(args[0]["state"], "play")
        self.assertEqual(args[0]["current_song"]["position"], 31)

        # Reset the mock
        mock_broker_manager.publish_state.reset_mock()

        # Test full update
        app.last_full_update_time = 0  # Force a full update

        # Check and update status
        with patch.object(app, '_update_player_state') as mock_update_player_state:
            app._check_and_update_status()

            # Check that the _update_player_state method was called
            mock_update_player_state.assert_called_once()


if __name__ == "__main__":
    unittest.main()
