"""
Integration tests for the MQTT Test Server.

This module contains integration tests for the MQTT Test Server component.
These tests require a running MQTT broker (Mosquitto) and MPD server.
"""

import unittest
import asyncio
import json
import sys
import os
import time
import subprocess
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from test_app.mqtt_test.server.server import MQTTTestServer

# Import the SDK modules
from amora_sdk.device.broker import (
    BrokerManager, BrokerConfig, ConnectionOptions, QoS,
    Message, StateMessage, CommandMessage, ResponseMessage
)
from amora_sdk.device.broker.topics import TopicType
from amora_sdk.device.player.music_player import MusicPlayer

# Import the mocks for partial mocking
from test_app.mqtt_test.tests.mocks import MockMusicPlayer

# Skip tests if MQTT broker or MPD server is not available
SKIP_TESTS = False
SKIP_REASON = ""

# Check if MQTT broker is running
try:
    import paho.mqtt.client as mqtt
    client = mqtt.Client()
    client.connect("localhost", 1883, 1)
    client.disconnect()
except Exception as e:
    SKIP_TESTS = True
    SKIP_REASON = f"MQTT broker not available: {e}"

# Check if MPD server is running
if not SKIP_TESTS:
    try:
        import mpd
        client = mpd.MPDClient()
        client.connect("localhost", 6600)
        client.disconnect()
    except Exception as e:
        SKIP_TESTS = True
        SKIP_REASON = f"MPD server not available: {e}"

@unittest.skipIf(SKIP_TESTS, SKIP_REASON)
class TestMQTTTestServerIntegration(unittest.TestCase):
    """Integration tests for the MQTT Test Server."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Create a temporary directory for music files
        cls.temp_dir = tempfile.mkdtemp()
        cls.music_dir = os.path.join(cls.temp_dir, "music")
        cls.playlists_dir = os.path.join(cls.temp_dir, "playlists")

        # Create directories
        os.makedirs(cls.music_dir, exist_ok=True)
        os.makedirs(cls.playlists_dir, exist_ok=True)

        # Create a test configuration
        cls.mqtt_config = {
            "broker_url": "localhost",
            "port": 1883,
            "device_id": "amora-test-device",
            "topic_prefix": "amora/test",
            "use_tls": False,
            "client_id": f"amora-test-server-{int(time.time())}"
        }

        cls.player_config = {
            "mpd_host": "localhost",
            "mpd_port": 6600,
            "storage_path": cls.music_dir,
            "playlists_path": cls.playlists_dir,
            "dev_mode": True
        }

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures that were used for all tests."""
        # Remove the temporary directory
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Set up test fixtures."""
        # Create a test client for receiving messages
        self.test_client = mqtt.Client(client_id=f"amora-test-client-{int(time.time())}")
        self.received_messages = []

        # Set up callbacks
        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"{self.mqtt_config['topic_prefix']}/{self.mqtt_config['device_id']}/#")

        def on_message(client, userdata, msg):
            self.received_messages.append((msg.topic, msg.payload))

        self.test_client.on_connect = on_connect
        self.test_client.on_message = on_message

        # Connect to the broker
        self.test_client.connect("localhost", 1883)
        self.test_client.loop_start()

        # Create server instance
        self.server = MQTTTestServer(self.mqtt_config, self.player_config)

        # Set up event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the server if it's running
        if self.server.running:
            self.loop.run_until_complete(self.server.stop())

        # Disconnect from the broker
        self.test_client.loop_stop()
        self.test_client.disconnect()

        # Close event loop
        self.loop.close()

    def test_server_start_stop(self):
        """Test server start and stop."""
        # Start the server
        self.loop.run_until_complete(self.server.start())

        # Check that the server is running
        self.assertTrue(self.server.running)
        self.assertTrue(self.server.player.connected)
        self.assertTrue(self.server.broker_manager.connected)

        # Wait for status updates
        time.sleep(2)

        # Check that status messages were published
        state_topics = [
            msg[0] for msg in self.received_messages
            if msg[0].endswith("/state")
        ]
        self.assertGreater(len(state_topics), 0)

        # Stop the server
        self.loop.run_until_complete(self.server.stop())

        # Check that the server is not running
        self.assertFalse(self.server.running)
        self.assertFalse(self.server.player.connected)

    def test_command_handling(self):
        """Test command handling."""
        # Start the server
        self.loop.run_until_complete(self.server.start())

        # Clear received messages
        self.received_messages = []

        # Create a command message
        command = CommandMessage(
            command="play",
            command_id="test-command-id",
            timestamp=time.time()
        )

        # Publish the command
        command_topic = f"{self.mqtt_config['topic_prefix']}/{self.mqtt_config['device_id']}/commands"
        self.test_client.publish(command_topic, command.to_json())

        # Wait for the response
        time.sleep(2)

        # Check that a response was published
        response_topics = [
            msg[0] for msg in self.received_messages
            if msg[0].endswith("/responses")
        ]
        self.assertGreater(len(response_topics), 0)

        # Parse the response
        response_payload = next(
            msg[1] for msg in self.received_messages
            if msg[0].endswith("/responses")
        )
        response_data = json.loads(response_payload)

        # Check the response
        self.assertEqual(response_data["command_id"], command.command_id)
        self.assertTrue(response_data["result"])
        self.assertEqual(response_data["message"], "Play command executed")

        # Stop the server
        self.loop.run_until_complete(self.server.stop())

    def test_status_updates(self):
        """Test status updates."""
        # Start the server
        self.loop.run_until_complete(self.server.start())

        # Clear received messages
        self.received_messages = []

        # Wait for status updates
        time.sleep(2)

        # Check that status messages were published
        state_topics = [
            msg[0] for msg in self.received_messages
            if msg[0].endswith("/state")
        ]
        self.assertGreater(len(state_topics), 0)

        # Parse the status message
        state_payload = next(
            msg[1] for msg in self.received_messages
            if msg[0].endswith("/state")
        )
        state_data = json.loads(state_payload)

        # Check the status
        self.assertIn("state", state_data)
        self.assertIn("volume", state_data)

        # Stop the server
        self.loop.run_until_complete(self.server.stop())

    def test_multiple_commands(self):
        """Test handling multiple commands."""
        # Start the server
        self.loop.run_until_complete(self.server.start())

        # Clear received messages
        self.received_messages = []

        # Create command messages
        commands = [
            CommandMessage(command="play", command_id="cmd1", timestamp=time.time()),
            CommandMessage(command="setVolume", command_id="cmd2", params={"volume": 75}, timestamp=time.time()),
            CommandMessage(command="pause", command_id="cmd3", timestamp=time.time()),
            CommandMessage(command="getStatus", command_id="cmd4", timestamp=time.time())
        ]

        # Publish the commands
        command_topic = f"{self.mqtt_config['topic_prefix']}/{self.mqtt_config['device_id']}/commands"
        for command in commands:
            self.test_client.publish(command_topic, command.to_json())
            time.sleep(0.5)  # Wait a bit between commands

        # Wait for the responses
        time.sleep(3)

        # Check that responses were published
        response_topics = [
            msg[0] for msg in self.received_messages
            if msg[0].endswith("/responses")
        ]
        self.assertEqual(len(response_topics), len(commands))

        # Parse the responses
        response_payloads = [
            json.loads(msg[1]) for msg in self.received_messages
            if msg[0].endswith("/responses")
        ]

        # Check the command IDs in the responses
        response_command_ids = [resp["command_id"] for resp in response_payloads]
        for command in commands:
            self.assertIn(command.command_id, response_command_ids)

        # Stop the server
        self.loop.run_until_complete(self.server.stop())

if __name__ == "__main__":
    unittest.main()
