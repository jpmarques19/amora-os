"""
Tests for the integration between BrokerManager and PlayerStatusUpdater.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import logging
import time

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the MPD client
sys.modules['mpd'] = MagicMock()
sys.modules['mpd'].MPDClient = MagicMock

# Mock the MQTT client
sys.modules['paho'] = MagicMock()
sys.modules['paho.mqtt'] = MagicMock()
sys.modules['paho.mqtt.client'] = MagicMock()

# Set MQTT_AVAILABLE to True
import amora_sdk.device.broker.client
amora_sdk.device.broker.client.MQTT_AVAILABLE = True

# Import the modules
from amora_sdk.device.broker.manager import BrokerManager
from amora_sdk.device.broker.config import BrokerConfig, ConnectionOptions, QoS
from amora_sdk.device.player.status_updater import PlayerStatusUpdater

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestStatusUpdaterIntegration(unittest.TestCase):
    """Tests for the integration between BrokerManager and PlayerStatusUpdater."""

    @patch('amora_sdk.device.broker.manager.MQTTClient')
    def setUp(self, mock_mqtt_client):
        """Set up the test."""
        self.mock_mqtt_client = mock_mqtt_client
        self.mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = self.mock_client_instance
        self.mock_client_instance.connect.return_value = True

        # Create a mock status updater
        self.mock_status_updater = MagicMock()
        self.mock_status_updater.start.return_value = True

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

        # Create a config with raw_config
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
            default_qos=QoS.AT_LEAST_ONCE,
            raw_config={
                "status_updater": {
                    "enabled": True,
                    "update_interval": 0.1,
                    "position_update_interval": 0.1,
                    "full_update_interval": 0.5
                }
            }
        )

    @patch('amora_sdk.device.broker.manager.PlayerStatusUpdater')
    def test_status_updater_initialization(self, mock_status_updater_class):
        """Test that the status updater is initialized when connecting."""
        # Configure the mock
        mock_status_updater = MagicMock()
        mock_status_updater_class.return_value = mock_status_updater

        # Create the broker manager with status updater enabled
        broker_manager = BrokerManager(self.config, self.mock_player, enable_status_updater=True)

        # Connect to the broker
        result = broker_manager.connect()

        # Check that the connection was successful
        self.assertTrue(result)

        # Check that the status updater was created with the correct parameters
        mock_status_updater_class.assert_called_once_with(
            player_interface=self.mock_player,
            broker_manager=broker_manager,
            config=self.config.raw_config
        )

        # Check that the status updater was started
        mock_status_updater.start.assert_called_once()

    @patch('amora_sdk.device.broker.manager.PlayerStatusUpdater')
    def test_status_updater_disabled(self, mock_status_updater_class):
        """Test that the status updater is not initialized when disabled."""
        # Create the broker manager with status updater disabled
        broker_manager = BrokerManager(self.config, self.mock_player, enable_status_updater=False)

        # Connect to the broker
        result = broker_manager.connect()

        # Check that the connection was successful
        self.assertTrue(result)

        # Check that the status updater was not created
        mock_status_updater_class.assert_not_called()

    def test_status_updater_stopped_on_disconnect(self):
        """Test that the status updater is stopped when disconnecting."""
        # Create the broker manager with status updater enabled
        broker_manager = BrokerManager(self.config, self.mock_player, enable_status_updater=True)

        # Set the status updater manually for testing
        broker_manager.status_updater = self.mock_status_updater

        # Disconnect from the broker
        broker_manager.disconnect()

        # Check that the status updater was stopped
        self.mock_status_updater.stop.assert_called_once()

        # Check that the status updater was set to None
        self.assertIsNone(broker_manager.status_updater)


if __name__ == '__main__':
    unittest.main()
