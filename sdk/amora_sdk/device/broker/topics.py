"""
Topic management utilities for the Broker module.
"""

import re
from enum import Enum
from typing import Optional, List, Set


class TopicType(Enum):
    """Types of topics used in the Broker module."""
    STATE = "state"
    COMMANDS = "commands"
    RESPONSES = "responses"
    CONNECTION = "connection"


class TopicManager:
    """
    Manages MQTT topics for the Broker module.
    
    This class provides utilities for creating, validating, and parsing topics
    based on the device ID namespace.
    """
    
    def __init__(self, topic_prefix: str, device_id: str):
        """
        Initialize the TopicManager.
        
        Args:
            topic_prefix: Prefix for all topics (e.g., 'amora/devices')
            device_id: Device ID
        """
        self.topic_prefix = topic_prefix
        self.device_id = device_id
        self._valid_topics: Set[str] = set()
        self._initialize_valid_topics()
    
    def _initialize_valid_topics(self) -> None:
        """Initialize the set of valid topics."""
        for topic_type in TopicType:
            self._valid_topics.add(self.get_topic(topic_type))
    
    def get_topic(self, topic_type: TopicType) -> str:
        """
        Get the full topic string for a given topic type.
        
        Args:
            topic_type: Type of the topic
            
        Returns:
            Full topic string
        """
        return f"{self.topic_prefix}/{self.device_id}/{topic_type.value}"
    
    def is_valid_topic(self, topic: str) -> bool:
        """
        Check if a topic is valid.
        
        Args:
            topic: Topic to check
            
        Returns:
            True if the topic is valid, False otherwise
        """
        return topic in self._valid_topics
    
    def parse_topic(self, topic: str) -> Optional[TopicType]:
        """
        Parse a topic string and return its type.
        
        Args:
            topic: Topic string to parse
            
        Returns:
            TopicType if the topic is valid, None otherwise
        """
        if not self.is_valid_topic(topic):
            return None
        
        # Extract the topic type from the topic string
        parts = topic.split('/')
        if len(parts) < 3:
            return None
        
        topic_type_str = parts[-1]
        try:
            return TopicType(topic_type_str)
        except ValueError:
            return None
    
    def get_subscription_topics(self) -> List[str]:
        """
        Get the list of topics to subscribe to.
        
        Returns:
            List of topics to subscribe to
        """
        return [self.get_topic(TopicType.COMMANDS)]
    
    def get_wildcard_topic(self) -> str:
        """
        Get a wildcard topic for the device.
        
        Returns:
            Wildcard topic string
        """
        return f"{self.topic_prefix}/{self.device_id}/#"
    
    def get_all_devices_wildcard(self) -> str:
        """
        Get a wildcard topic for all devices.
        
        Returns:
            Wildcard topic string for all devices
        """
        return f"{self.topic_prefix}/+/#"
