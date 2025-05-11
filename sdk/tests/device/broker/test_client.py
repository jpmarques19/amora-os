"""
Tests for the MQTT client wrapper.
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
from amora_sdk.device.broker.client import MQTTClient
from amora_sdk.device.broker.config import ConnectionOptions, QoS

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestMQTTClient(unittest.TestCase):
    """Tests for the MQTTClient class."""
    
    @patch('amora_sdk.device.broker.client.mqtt')
    def setUp(self, mock_mqtt):
        """Set up the test."""
        self.mock_mqtt = mock_mqtt
        self.mock_client = MagicMock()
        mock_mqtt.Client.return_value = self.mock_client
        
        self.options = ConnectionOptions(
            use_tls=False,
            username="test_user",
            password="test_password",
            keep_alive=30,
            clean_session=True,
            reconnect_on_failure=True,
            max_reconnect_delay=60
        )
        
        self.client = MQTTClient(
            client_id="test_client",
            broker_url="test.broker.com",
            port=1883,
            options=self.options
        )
    
    def test_init(self):
        """Test initialization."""
        # Check that the MQTT client was created with the correct parameters
        self.mock_mqtt.Client.assert_called_once_with(
            client_id="test_client",
            clean_session=True
        )
        
        # Check that the callbacks were set
        self.assertEqual(self.mock_client.on_connect, self.client._on_connect)
        self.assertEqual(self.mock_client.on_disconnect, self.client._on_disconnect)
        self.assertEqual(self.mock_client.on_message, self.client._on_message)
        self.assertEqual(self.mock_client.on_publish, self.client._on_publish)
        self.assertEqual(self.mock_client.on_subscribe, self.client._on_subscribe)
        
        # Check that the username and password were set
        self.mock_client.username_pw_set.assert_called_once_with(
            "test_user",
            "test_password"
        )
    
    def test_connect(self):
        """Test connect method."""
        # Call the connect method
        result = self.client.connect()
        
        # Check that the MQTT client's connect method was called with the correct parameters
        self.mock_client.connect.assert_called_once_with(
            "test.broker.com",
            1883,
            keepalive=30
        )
        
        # Check that the MQTT client's loop_start method was called
        self.mock_client.loop_start.assert_called_once()
        
        # Check that the method returned True
        self.assertTrue(result)
    
    def test_connect_error(self):
        """Test connect method with error."""
        # Make the MQTT client's connect method raise an exception
        self.mock_client.connect.side_effect = Exception("Connection error")
        
        # Call the connect method
        result = self.client.connect()
        
        # Check that the MQTT client's connect method was called
        self.mock_client.connect.assert_called_once()
        
        # Check that the MQTT client's loop_start method was not called
        self.mock_client.loop_start.assert_not_called()
        
        # Check that the method returned False
        self.assertFalse(result)
    
    def test_disconnect(self):
        """Test disconnect method."""
        # Call the disconnect method
        self.client.disconnect()
        
        # Check that the MQTT client's disconnect method was called
        self.mock_client.disconnect.assert_called_once()
        
        # Check that the MQTT client's loop_stop method was called
        self.mock_client.loop_stop.assert_called_once()
    
    def test_publish(self):
        """Test publish method."""
        # Set up the MQTT client's publish method to return a successful result
        mock_result = MagicMock()
        mock_result.rc = 0  # MQTT_ERR_SUCCESS
        self.mock_client.publish.return_value = mock_result
        
        # Set the client as connected
        self.client.connected = True
        
        # Call the publish method with a dictionary payload
        result = self.client.publish(
            topic="test/topic",
            payload={"key": "value"},
            qos=QoS.AT_LEAST_ONCE,
            retain=True
        )
        
        # Check that the MQTT client's publish method was called with the correct parameters
        self.mock_client.publish.assert_called_once()
        args, kwargs = self.mock_client.publish.call_args
        self.assertEqual(args[0], "test/topic")
        self.assertEqual(json.loads(args[1].decode('utf-8')), {"key": "value"})
        self.assertEqual(args[2], 1)  # QoS.AT_LEAST_ONCE.value
        self.assertEqual(args[3], True)
        
        # Check that the method returned True
        self.assertTrue(result)
    
    def test_subscribe(self):
        """Test subscribe method."""
        # Set up the MQTT client's subscribe method to return a successful result
        self.mock_client.subscribe.return_value = (0, 1)  # (MQTT_ERR_SUCCESS, granted_qos)
        
        # Set the client as connected
        self.client.connected = True
        
        # Create a callback function
        callback = MagicMock()
        
        # Call the subscribe method
        result = self.client.subscribe(
            topic="test/topic",
            qos=QoS.AT_LEAST_ONCE,
            callback=callback
        )
        
        # Check that the MQTT client's subscribe method was called with the correct parameters
        self.mock_client.subscribe.assert_called_once_with("test/topic", 1)
        
        # Check that the callback was registered
        self.assertIn("test/topic", self.client.on_message_callbacks)
        self.assertIn(callback, self.client.on_message_callbacks["test/topic"])
        
        # Check that the method returned True
        self.assertTrue(result)
    
    def test_unsubscribe(self):
        """Test unsubscribe method."""
        # Set up the MQTT client's unsubscribe method to return a successful result
        self.mock_client.unsubscribe.return_value = (0,)  # (MQTT_ERR_SUCCESS,)
        
        # Set the client as connected
        self.client.connected = True
        
        # Register a callback
        self.client.on_message_callbacks["test/topic"] = [MagicMock()]
        
        # Call the unsubscribe method
        result = self.client.unsubscribe("test/topic")
        
        # Check that the MQTT client's unsubscribe method was called with the correct parameters
        self.mock_client.unsubscribe.assert_called_once_with("test/topic")
        
        # Check that the callback was unregistered
        self.assertNotIn("test/topic", self.client.on_message_callbacks)
        
        # Check that the method returned True
        self.assertTrue(result)
    
    def test_set_last_will(self):
        """Test set_last_will method."""
        # Call the set_last_will method
        self.client.set_last_will(
            topic="test/topic",
            payload={"status": "offline"},
            qos=QoS.AT_LEAST_ONCE,
            retain=True
        )
        
        # Check that the MQTT client's will_set method was called with the correct parameters
        self.mock_client.will_set.assert_called_once()
        args, kwargs = self.mock_client.will_set.call_args
        self.assertEqual(args[0], "test/topic")
        self.assertEqual(json.loads(args[1].decode('utf-8')), {"status": "offline"})
        self.assertEqual(args[2], 1)  # QoS.AT_LEAST_ONCE.value
        self.assertEqual(args[3], True)


if __name__ == '__main__':
    unittest.main()
