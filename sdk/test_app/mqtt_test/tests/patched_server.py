"""
Patched server module for testing.

This module provides a patched version of the server module for testing.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import the mock SDK modules
from tests.mock_sdk import (
    BrokerManager, BrokerConfig, ConnectionOptions, QoS,
    Message, StateMessage, CommandMessage, ResponseMessage,
    TopicType, MusicPlayer
)

# Import the original server module
from server.server import MQTTTestServer as OriginalMQTTTestServer

# Create a patched version of the server module
class MQTTTestServer(OriginalMQTTTestServer):
    """Patched version of the MQTTTestServer class for testing."""
    
    def __init__(self, mqtt_config, player_config):
        """Initialize the patched server."""
        # Save the configuration
        self.mqtt_config = mqtt_config
        self.player_config = player_config
        
        # Create player interface
        self.player = self._create_player()
        
        # Create broker manager
        self.broker_manager = self._create_broker_manager()
        
        # Set up command handlers
        self._setup_command_handlers()
        
        # Status update interval in seconds
        self.status_update_interval = 1.0
        
        # Running flag
        self.running = False
        
        # Status update task
        self.status_update_task = None
