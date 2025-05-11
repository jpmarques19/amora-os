"""
Base test class for integration tests.
"""

import os
import sys
import logging
import pytest
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import configuration
from integration_tests.config import load_config, create_test_directories, cleanup_test_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseIntegrationTest:
    """Base class for integration tests."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        logger.info(f"Setting up {cls.__name__}")

        # Load configuration
        cls.config = load_config()

        # Create test directories
        create_test_directories()

        # Check if we have the required configuration
        cls._check_config()

    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        logger.info(f"Tearing down {cls.__name__}")

        # Clean up test directories
        cleanup_test_directories()

    @classmethod
    def _check_config(cls):
        """Check if we have the required configuration."""
        # This method should be overridden by subclasses
        pass

class MPDIntegrationTest(BaseIntegrationTest):
    """Base class for MPD integration tests."""

    @classmethod
    def _check_config(cls):
        """Check if we have the required configuration for MPD tests."""
        # Check MPD host and port
        if not cls.config["mpd"]["host"]:
            pytest.skip("MPD host not configured")

        # Check if MPD is running
        try:
            from mpd import MPDClient
            client = MPDClient()
            client.connect(cls.config["mpd"]["host"], cls.config["mpd"]["port"])
            client.ping()
            client.disconnect()
            logger.info(f"MPD is running at {cls.config['mpd']['host']}:{cls.config['mpd']['port']}")
        except Exception as e:
            pytest.skip(f"MPD is not running: {e}")

class AzureIntegrationTest(BaseIntegrationTest):
    """Base class for Azure integration tests."""

    @classmethod
    def _check_config(cls):
        """Check if we have the required configuration for Azure tests."""
        # Check IoT Hub connection string
        if not cls.config["azure"]["iot_hub_connection_string"]:
            pytest.skip("Azure IoT Hub connection string not configured")

        # Check Event Hub connection string
        if not cls.config["azure"]["event_hub_connection_string"]:
            pytest.skip("Azure Event Hub connection string not configured")

        # Check if we can connect to Azure IoT Hub
        try:
            # Import here to avoid dependency issues
            from azure.iot.device import IoTHubDeviceClient

            # Create client
            client = IoTHubDeviceClient.create_from_connection_string(
                cls.config["azure"]["iot_hub_connection_string"]
            )

            # Connect to IoT Hub
            client.connect()
            logger.info("Connected to Azure IoT Hub")

            # Disconnect
            client.disconnect()
            logger.info("Disconnected from Azure IoT Hub")
        except Exception as e:
            pytest.skip(f"Failed to connect to Azure IoT Hub: {e}")

class PlayerIntegrationTest(MPDIntegrationTest):
    """Base class for player integration tests."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        super().setup_class()

        # Import player module
        from amora_sdk.device.player import MusicPlayer

        # Create player instance
        cls.player = MusicPlayer(cls.config)

        # Connect to MPD
        if not cls.player.connect():
            pytest.skip("Failed to connect to MPD")

    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        # Disconnect from MPD
        if hasattr(cls, "player") and cls.player.connected:
            cls.player.disconnect()

        super().teardown_class()

class IoTDeviceIntegrationTest(AzureIntegrationTest, MPDIntegrationTest):
    """Base class for IoT device integration tests."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        super().setup_class()

        # Import IoT client module
        from amora_sdk.device.iot import IoTDeviceClient
        from unittest.mock import MagicMock

        # Create mock player interface
        cls.player_interface = MagicMock()

        # Set up default return values for player interface methods
        cls.player_interface.play = MagicMock(return_value=True)
        cls.player_interface.pause = MagicMock(return_value=True)
        cls.player_interface.stop = MagicMock(return_value=True)
        cls.player_interface.next = MagicMock(return_value=True)
        cls.player_interface.previous = MagicMock(return_value=True)
        cls.player_interface.set_volume = MagicMock(return_value=True)
        cls.player_interface.get_status = MagicMock(return_value={"state": "playing", "volume": 80})
        cls.player_interface.get_playlists = MagicMock(return_value=["Test Playlist 1", "Test Playlist 2"])
        cls.player_interface.play_playlist = MagicMock(return_value=True)
        cls.player_interface.set_repeat = MagicMock(return_value=True)
        cls.player_interface.set_random = MagicMock(return_value=True)

        # Create IoT client
        cls.iot_client = IoTDeviceClient(
            cls.config["azure"]["iot_hub_connection_string"],
            cls.player_interface
        )

    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        # Disconnect from IoT Hub
        if hasattr(cls, "iot_client"):
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(cls.iot_client.disconnect())

        super().teardown_class()
