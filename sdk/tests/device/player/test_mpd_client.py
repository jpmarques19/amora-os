"""
Tests for the MPDClientWrapper class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the module to test
from amora_sdk.device.player.mpd_client import MPDClientWrapper
from tests.mocks.mock_mpd import MockMPDClient


class TestMPDClientWrapper(unittest.TestCase):
    """Test cases for the MPD Client Wrapper."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock MPD client
        self.mock_mpd_client = MockMPDClient()

        # Create the MPD client patcher
        self.mpd_patcher = patch('mpd.MPDClient', return_value=self.mock_mpd_client)
        self.mock_mpd_class = self.mpd_patcher.start()

        # Create the wrapper instance
        self.wrapper = MPDClientWrapper(host="localhost", port=6600, timeout=10)
        self.wrapper.client = self.mock_mpd_client

    def tearDown(self):
        """Clean up after tests."""
        self.mpd_patcher.stop()

    def test_init(self):
        """Test initialization."""
        wrapper = MPDClientWrapper(host="test_host", port=1234, timeout=5)
        self.assertEqual(wrapper.host, "test_host")
        self.assertEqual(wrapper.port, 1234)
        self.assertEqual(wrapper.timeout, 5)
        self.assertEqual(wrapper.client.timeout, 5)
        self.assertFalse(wrapper.connected)
        self.assertEqual(wrapper.max_retries, 3)
        self.assertEqual(wrapper.retry_delay, 1)

    def test_connect_success(self):
        """Test successful connection."""
        # Reset the wrapper's connection state
        self.wrapper.connected = False

        # Call the method
        result = self.wrapper.connect()

        # Verify the results
        self.assertTrue(result)
        self.assertTrue(self.wrapper.connected)
        self.assertTrue(self.mock_mpd_client.connected)

    def test_connect_already_connected(self):
        """Test connect when already connected."""
        # Set the wrapper as connected
        self.wrapper.connected = True

        # Call the method
        result = self.wrapper.connect()

        # Verify the results
        self.assertTrue(result)
        # The MPD client's connect method should not be called
        self.assertFalse(self.mock_mpd_client.connected)

    def test_connect_failure(self):
        """Test failed connection."""
        # Reset the wrapper's connection state
        self.wrapper.connected = False

        # Configure the mock to raise an exception
        self.mock_mpd_client.connect = MagicMock(side_effect=Exception("Connection failed"))

        # Call the method
        result = self.wrapper.connect()

        # Verify the results
        self.assertFalse(result)
        self.assertFalse(self.wrapper.connected)

    def test_disconnect(self):
        """Test disconnect method."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True
        self.mock_mpd_client.connected = True

        # Call the method
        self.wrapper.disconnect()

        # Verify the results
        self.assertFalse(self.wrapper.connected)
        self.assertFalse(self.mock_mpd_client.connected)

    def test_disconnect_not_connected(self):
        """Test disconnect when not connected."""
        # Ensure the wrapper is not connected
        self.wrapper.connected = False

        # Ensure the mock client is connected
        self.mock_mpd_client.connected = True

        # Call the method
        self.wrapper.disconnect()

        # Verify the results
        self.assertFalse(self.wrapper.connected)
        # The MPD client's disconnect method should not be called
        self.assertTrue(self.mock_mpd_client.connected)

    def test_disconnect_error(self):
        """Test disconnect with error."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True

        # Configure the mock to raise an exception
        self.mock_mpd_client.close = MagicMock(side_effect=Exception("Disconnect error"))

        # Call the method
        self.wrapper.disconnect()

        # Verify the results
        self.assertFalse(self.wrapper.connected)

    def test_reconnect(self):
        """Test reconnect method."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True
        self.mock_mpd_client.connected = True

        # Call the method
        result = self.wrapper.reconnect()

        # Verify the results
        self.assertTrue(result)
        self.assertTrue(self.wrapper.connected)
        self.assertTrue(self.mock_mpd_client.connected)

    def test_ensure_connected_already_connected(self):
        """Test _ensure_connected when already connected."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True
        self.mock_mpd_client.connected = True

        # Call the method
        result = self.wrapper._ensure_connected()

        # Verify the results
        self.assertTrue(result)

    def test_ensure_connected_reconnect(self):
        """Test _ensure_connected when reconnection needed."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True

        # Configure the mock to raise an exception
        self.mock_mpd_client.ping = MagicMock(side_effect=Exception("Connection lost"))

        # Mock the reconnect method
        with patch.object(self.wrapper, 'reconnect', return_value=True) as mock_reconnect:
            # Call the method
            result = self.wrapper._ensure_connected()

            # Verify the results
            self.assertTrue(result)
            mock_reconnect.assert_called_once()

    def test_ensure_connected_not_connected(self):
        """Test _ensure_connected when not connected."""
        # Ensure the wrapper is not connected
        self.wrapper.connected = False

        # Mock the connect method
        with patch.object(self.wrapper, 'connect', return_value=True) as mock_connect:
            # Call the method
            result = self.wrapper._ensure_connected()

            # Verify the results
            self.assertTrue(result)
            mock_connect.assert_called_once()

    def test_execute_command_success(self):
        """Test _execute_command with successful execution."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True
        self.mock_mpd_client.connected = True

        # Configure the mock
        self.mock_mpd_client.status = MagicMock(return_value={"state": "play"})

        # Call the method
        result = self.wrapper._execute_command("status")

        # Verify the results
        self.assertEqual(result, {"state": "play"})
        self.mock_mpd_client.status.assert_called_once()

    def test_execute_command_retry_success(self):
        """Test _execute_command with retry and successful execution."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True

        # Configure the mock to fail once then succeed
        self.mock_mpd_client.status = MagicMock(side_effect=[Exception("Command failed"), {"state": "play"}])

        # Mock the reconnect method
        with patch.object(self.wrapper, 'reconnect', return_value=True):
            # Call the method
            result = self.wrapper._execute_command("status")

            # Verify the results
            self.assertEqual(result, {"state": "play"})
            self.assertEqual(self.mock_mpd_client.status.call_count, 2)

    def test_execute_command_all_retries_fail(self):
        """Test _execute_command when all retries fail."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True

        # Configure the mock to always fail
        error = Exception("Command failed")
        self.mock_mpd_client.status = MagicMock(side_effect=error)

        # Mock the reconnect method
        with patch.object(self.wrapper, 'reconnect', return_value=True):
            # Call the method and expect an exception
            with self.assertRaises(Exception) as context:
                self.wrapper._execute_command("status")

            # Verify the results
            self.assertEqual(str(context.exception), "Command failed")
            self.assertEqual(self.mock_mpd_client.status.call_count, 3)  # 3 retries

    def test_getattr(self):
        """Test __getattr__ method."""
        # Ensure the wrapper is connected
        self.wrapper.connected = True
        self.mock_mpd_client.connected = True

        # Configure the mock
        self.mock_mpd_client.play = MagicMock()

        # Call a method through __getattr__
        self.wrapper.play()

        # Verify the results
        self.mock_mpd_client.play.assert_called_once()

    def test_getattr_invalid_attribute(self):
        """Test __getattr__ with invalid attribute."""
        # Call __getattr__ with an invalid attribute
        with self.assertRaises(AttributeError):
            self.wrapper.invalid_method()


if __name__ == "__main__":
    unittest.main()
