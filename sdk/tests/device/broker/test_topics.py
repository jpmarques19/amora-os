"""
Tests for the TopicManager class.
"""

import unittest
import sys
import os
import logging

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the module
from amora_sdk.device.broker.topics import TopicManager, TopicType

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestTopicManager(unittest.TestCase):
    """Tests for the TopicManager class."""
    
    def setUp(self):
        """Set up the test."""
        self.topic_prefix = "amora/devices"
        self.device_id = "test_device"
        self.topic_manager = TopicManager(self.topic_prefix, self.device_id)
    
    def test_get_topic(self):
        """Test get_topic method."""
        # Test getting the state topic
        state_topic = self.topic_manager.get_topic(TopicType.STATE)
        self.assertEqual(state_topic, "amora/devices/test_device/state")
        
        # Test getting the commands topic
        commands_topic = self.topic_manager.get_topic(TopicType.COMMANDS)
        self.assertEqual(commands_topic, "amora/devices/test_device/commands")
        
        # Test getting the responses topic
        responses_topic = self.topic_manager.get_topic(TopicType.RESPONSES)
        self.assertEqual(responses_topic, "amora/devices/test_device/responses")
        
        # Test getting the connection topic
        connection_topic = self.topic_manager.get_topic(TopicType.CONNECTION)
        self.assertEqual(connection_topic, "amora/devices/test_device/connection")
    
    def test_is_valid_topic(self):
        """Test is_valid_topic method."""
        # Test valid topics
        self.assertTrue(self.topic_manager.is_valid_topic("amora/devices/test_device/state"))
        self.assertTrue(self.topic_manager.is_valid_topic("amora/devices/test_device/commands"))
        self.assertTrue(self.topic_manager.is_valid_topic("amora/devices/test_device/responses"))
        self.assertTrue(self.topic_manager.is_valid_topic("amora/devices/test_device/connection"))
        
        # Test invalid topics
        self.assertFalse(self.topic_manager.is_valid_topic("amora/devices/test_device/invalid"))
        self.assertFalse(self.topic_manager.is_valid_topic("amora/devices/other_device/state"))
        self.assertFalse(self.topic_manager.is_valid_topic("invalid/topic"))
    
    def test_parse_topic(self):
        """Test parse_topic method."""
        # Test parsing valid topics
        self.assertEqual(
            self.topic_manager.parse_topic("amora/devices/test_device/state"),
            TopicType.STATE
        )
        self.assertEqual(
            self.topic_manager.parse_topic("amora/devices/test_device/commands"),
            TopicType.COMMANDS
        )
        self.assertEqual(
            self.topic_manager.parse_topic("amora/devices/test_device/responses"),
            TopicType.RESPONSES
        )
        self.assertEqual(
            self.topic_manager.parse_topic("amora/devices/test_device/connection"),
            TopicType.CONNECTION
        )
        
        # Test parsing invalid topics
        self.assertIsNone(self.topic_manager.parse_topic("amora/devices/test_device/invalid"))
        self.assertIsNone(self.topic_manager.parse_topic("amora/devices/other_device/state"))
        self.assertIsNone(self.topic_manager.parse_topic("invalid/topic"))
    
    def test_get_subscription_topics(self):
        """Test get_subscription_topics method."""
        subscription_topics = self.topic_manager.get_subscription_topics()
        self.assertEqual(len(subscription_topics), 1)
        self.assertIn("amora/devices/test_device/commands", subscription_topics)
    
    def test_get_wildcard_topic(self):
        """Test get_wildcard_topic method."""
        wildcard_topic = self.topic_manager.get_wildcard_topic()
        self.assertEqual(wildcard_topic, "amora/devices/test_device/#")
    
    def test_get_all_devices_wildcard(self):
        """Test get_all_devices_wildcard method."""
        all_devices_wildcard = self.topic_manager.get_all_devices_wildcard()
        self.assertEqual(all_devices_wildcard, "amora/devices/+/#")


if __name__ == '__main__':
    unittest.main()
