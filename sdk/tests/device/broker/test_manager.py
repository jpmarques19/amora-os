"""
Tests for the BrokerManager class.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import logging

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the module
from amora_sdk.device.broker.manager import BrokerManager
from amora_sdk.device.broker.config import BrokerConfig, ConnectionOptions, QoS
from amora_sdk.device.broker.topics import TopicType
from amora_sdk.device.broker.messages import CommandMessage, ResponseMessage, StateMessage

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestBrokerManager(unittest.TestCase):
    """Tests for the BrokerManager class."""

    @patch('amora_sdk.device.broker.manager.MQTTClient')
    def setUp(self, mock_mqtt_client):
        """Set up the test."""
        self.mock_mqtt_client = mock_mqtt_client
        self.mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = self.mock_client_instance

        # Create a mock player interface
        self.mock_player = MagicMock()
        self.mock_player.get_status.return_value = {
            'state': 'play',
            'current_song': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'position': 30,
                'duration': 180
            },
            'volume': 80,
            'repeat': False,
            'random': False
        }

        # Create a config
        self.config = BrokerConfig(
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
            default_qos=QoS.AT_LEAST_ONCE
        )

        # Create the broker manager
        self.broker_manager = BrokerManager(self.config, self.mock_player)

    def test_init(self):
        """Test initialization."""
        # Check that the MQTT client was created with the correct parameters
        self.mock_mqtt_client.assert_called_once_with(
            client_id="test_client",
            broker_url="test.broker.com",
            port=1883,
            options=self.config.connection_options
        )

        # Check that the callbacks were registered
        self.mock_client_instance.register_on_connect.assert_called_once_with(
            self.broker_manager._on_connect
        )
        self.mock_client_instance.register_on_disconnect.assert_called_once_with(
            self.broker_manager._on_disconnect
        )

        # Check that the last will message was set
        self.mock_client_instance.set_last_will.assert_called_once()

    def test_connect(self):
        """Test connect method."""
        # Call the connect method
        result = self.broker_manager.connect()

        # Check that the MQTT client's connect method was called
        self.mock_client_instance.connect.assert_called_once()

        # Check that the method returned the result from the MQTT client
        self.assertEqual(result, self.mock_client_instance.connect.return_value)

    def test_disconnect(self):
        """Test disconnect method."""
        # Call the disconnect method
        self.broker_manager.disconnect()

        # Check that the MQTT client's disconnect method was called
        self.mock_client_instance.disconnect.assert_called_once()

    def test_on_connect(self):
        """Test _on_connect method."""
        # Call the _on_connect method with success=True
        self.broker_manager._on_connect(True)

        # Check that the connected flag was set
        self.assertTrue(self.broker_manager.connected)

        # Check that the MQTT client's subscribe method was called
        self.mock_client_instance.subscribe.assert_called_once_with(
            topic="amora/devices/test_device/commands",
            qos=QoS.AT_LEAST_ONCE,
            callback=self.broker_manager._on_command_received
        )

        # Check that the connection status was published
        self.mock_client_instance.publish.assert_called_once()

    def test_on_disconnect(self):
        """Test _on_disconnect method."""
        # Set the connected flag
        self.broker_manager.connected = True

        # Call the _on_disconnect method
        self.broker_manager._on_disconnect()

        # Check that the connected flag was cleared
        self.assertFalse(self.broker_manager.connected)

    def test_on_command_received(self):
        """Test _on_command_received method."""
        # Create a command message
        command_json = json.dumps({
            "command": "play",
            "command_id": "test_id",
            "params": {},
            "timestamp": 123456789
        })

        # Mock the _execute_command method
        self.broker_manager._execute_command = MagicMock()
        self.broker_manager._execute_command.return_value = ResponseMessage(
            command_id="test_id",
            result=True,
            message="Command executed"
        )

        # Mock the publish_response method
        self.broker_manager.publish_response = MagicMock()

        # Call the _on_command_received method
        self.broker_manager._on_command_received(
            "amora/devices/test_device/commands",
            command_json.encode('utf-8'),
            {"qos": 1, "retain": False}
        )

        # Check that the _execute_command method was called with the correct parameters
        self.broker_manager._execute_command.assert_called_once()
        args, kwargs = self.broker_manager._execute_command.call_args
        self.assertEqual(args[0].command, "play")
        self.assertEqual(args[0].command_id, "test_id")

        # Check that the publish_response method was called with the correct parameters
        self.broker_manager.publish_response.assert_called_once_with(
            self.broker_manager._execute_command.return_value
        )

    def test_execute_command_with_handler(self):
        """Test _execute_command method with a registered handler."""
        # Create a command message
        command_msg = CommandMessage(
            command="test_command",
            command_id="test_id",
            params={"param1": "value1"}
        )

        # Create a mock handler
        mock_handler = MagicMock()
        mock_handler.return_value = ResponseMessage(
            command_id="test_id",
            result=True,
            message="Command executed"
        )

        # Register the handler
        self.broker_manager.register_command_handler("test_command", mock_handler)

        # Call the _execute_command method
        response = self.broker_manager._execute_command(command_msg)

        # Check that the handler was called with the correct parameters
        mock_handler.assert_called_once_with(command_msg)

        # Check that the response is correct
        self.assertEqual(response.command_id, "test_id")
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Command executed")

    def test_execute_command_with_player_interface(self):
        """Test _execute_command method with the player interface."""
        # Create a command message
        command_msg = CommandMessage(
            command="play",
            command_id="test_id",
            params={}
        )

        # Set up the player interface
        self.mock_player.play.return_value = True

        # Call the _execute_command method
        response = self.broker_manager._execute_command(command_msg)

        # Check that the player interface method was called
        self.mock_player.play.assert_called_once_with()

        # Check that the response is correct
        self.assertEqual(response.command_id, "test_id")
        self.assertTrue(response.result)
        self.assertEqual(response.message, "Command play executed")

    def test_publish_state(self):
        """Test publish_state method."""
        # Create a state dictionary
        state = {
            'state': 'play',
            'current_song': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'position': 30,
                'duration': 180
            },
            'volume': 80,
            'repeat': False,
            'random': False
        }

        # Register a state change callback
        mock_callback = MagicMock()
        self.broker_manager.register_state_change_callback(mock_callback)

        # Call the publish_state method
        self.broker_manager.publish_state(state)

        # Check that the callback was called with the correct parameters
        mock_callback.assert_called_once()
        args, kwargs = mock_callback.call_args
        self.assertEqual(args[0].state, "play")
        self.assertEqual(args[0].volume, 80)

        # Check that the MQTT client's publish method was called with the correct parameters
        self.mock_client_instance.publish.assert_called_once()

    def test_update_player_state(self):
        """Test update_player_state method."""
        # Mock the publish_state method
        self.broker_manager.publish_state = MagicMock()

        # Call the update_player_state method
        result = self.broker_manager.update_player_state()

        # Check that the player interface's get_status method was called
        self.mock_player.get_status.assert_called_once()

        # Check that the publish_state method was called with the correct parameters
        self.broker_manager.publish_state.assert_called_once_with(
            self.mock_player.get_status.return_value
        )

        # Check that the method returned the result from publish_state
        self.assertEqual(result, self.broker_manager.publish_state.return_value)


if __name__ == '__main__':
    unittest.main()
