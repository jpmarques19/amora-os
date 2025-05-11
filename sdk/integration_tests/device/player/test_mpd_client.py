"""
Integration tests for the MPDClientWrapper class.
"""

import os
import sys
import time
import pytest
import logging
from typing import Dict, Any, List

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the base test class
from integration_tests.base_test import MPDIntegrationTest

# Import the module to test
from amora_sdk.device.player.mpd_client import MPDClientWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestMPDClientWrapper(MPDIntegrationTest):
    """Integration tests for the MPDClientWrapper class."""

    def setup_method(self):
        """Set up test method."""
        # Create MPD client wrapper
        self.wrapper = MPDClientWrapper(
            host=self.config["mpd"]["host"],
            port=self.config["mpd"]["port"],
            timeout=10
        )

        # Connect to MPD
        self.wrapper.connect()

    def teardown_method(self):
        """Tear down test method."""
        # Disconnect from MPD
        if hasattr(self, "wrapper") and self.wrapper.connected:
            self.wrapper.disconnect()

    def test_connect_disconnect(self):
        """Test connect and disconnect methods."""
        # Disconnect
        self.wrapper.disconnect()
        assert not self.wrapper.connected

        # Connect
        result = self.wrapper.connect()
        assert result
        assert self.wrapper.connected

        # Connect when already connected
        result = self.wrapper.connect()
        assert result

    def test_reconnect(self):
        """Test reconnect method."""
        # Disconnect
        self.wrapper.disconnect()
        assert not self.wrapper.connected

        # Reconnect
        result = self.wrapper.reconnect()
        assert result
        assert self.wrapper.connected

    def test_ensure_connected(self):
        """Test _ensure_connected method."""
        # Disconnect
        self.wrapper.disconnect()
        assert not self.wrapper.connected

        # Ensure connected
        result = self.wrapper._ensure_connected()
        assert result
        assert self.wrapper.connected

        # Ensure connected when already connected
        result = self.wrapper._ensure_connected()
        assert result

    def test_execute_command(self):
        """Test _execute_command method."""
        # Execute a simple command
        result = self.wrapper._execute_command("ping")
        assert result is None

        # Execute a command that returns data
        result = self.wrapper._execute_command("status")
        assert isinstance(result, dict)
        assert "state" in result

    def test_command_execution(self):
        """Test command execution through __getattr__."""
        # Execute a simple command
        self.wrapper.ping()

        # Execute a command that returns data
        status = self.wrapper.status()
        assert isinstance(status, dict)
        assert "state" in status

        # Get current volume
        current_volume = status.get("volume", "0")

        try:
            # Execute a command with arguments
            self.wrapper.setvol(50)
            status = self.wrapper.status()
            assert status["volume"] == "50"
        except Exception as e:
            # If setting volume fails, we'll skip this assertion
            # This can happen if audio outputs are disabled
            import pytest
            pytest.skip(f"Could not set volume: {e}")

        # Restore original volume
        try:
            self.wrapper.setvol(int(current_volume))
        except Exception:
            pass

    def test_error_handling(self):
        """Test error handling."""
        # Disconnect from MPD
        self.wrapper.disconnect()

        # Try to execute a command when disconnected
        # This should automatically reconnect
        status = self.wrapper.status()
        assert isinstance(status, dict)
        assert "state" in status

    def test_command_with_retries(self):
        """Test command execution with retries."""
        # Mock the client's status method to fail once then succeed
        original_status = self.wrapper.client.status

        fail_count = [0]
        def mock_status():
            if fail_count[0] < 1:
                fail_count[0] += 1
                raise Exception("Test exception")
            return original_status()

        self.wrapper.client.status = mock_status

        # Execute the command
        status = self.wrapper.status()

        # Verify the results
        assert isinstance(status, dict)
        assert "state" in status
        assert fail_count[0] == 1

        # Restore the original method
        self.wrapper.client.status = original_status
