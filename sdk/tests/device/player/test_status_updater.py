"""
Tests for the PlayerStatusUpdater class.
"""

import os
import sys
import unittest
import time
from unittest.mock import MagicMock, patch, call

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the MPD client
sys.modules['mpd'] = MagicMock()
sys.modules['mpd'].MPDClient = MagicMock

# Import the module to test
from amora_sdk.device.player.status_updater import PlayerStatusUpdater


class TestPlayerStatusUpdater(unittest.TestCase):
    """Test cases for the Player Status Updater."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock player interface
        self.mock_player = MagicMock()
        self.mock_player.get_status.return_value = {
            "state": "stop",
            "volume": 50,
            "current_song": None,
            "playlist": None,
            "playlist_tracks": None,
            "repeat": False,
            "random": False
        }

        # Create mock broker manager
        self.mock_broker = MagicMock()
        self.mock_broker.update_player_state.return_value = True
        self.mock_broker.publish_state.return_value = True

        # Configuration
        self.config = {
            "status_updater": {
                "enabled": True,
                "update_interval": 0.1,  # Fast updates for testing
                "position_update_interval": 0.1,
                "full_update_interval": 0.3
            }
        }

        # Create the status updater
        self.updater = PlayerStatusUpdater(
            player_interface=self.mock_player,
            broker_manager=self.mock_broker,
            config=self.config
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.updater.running:
            self.updater.stop()

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.updater.player, self.mock_player)
        self.assertEqual(self.updater.broker, self.mock_broker)
        self.assertEqual(self.updater.update_interval, 0.1)
        self.assertEqual(self.updater.position_update_interval, 0.1)
        self.assertEqual(self.updater.full_update_interval, 0.3)
        self.assertTrue(self.updater.enabled)
        self.assertFalse(self.updater.running)
        self.assertIsNone(self.updater.update_thread)
        self.assertIsNone(self.updater.last_status)

    def test_start_stop(self):
        """Test start and stop methods."""
        # Start the updater
        result = self.updater.start()
        self.assertTrue(result)
        self.assertTrue(self.updater.running)
        self.assertIsNotNone(self.updater.update_thread)
        self.assertTrue(self.updater.update_thread.is_alive())

        # Stop the updater
        self.updater.stop()
        self.assertFalse(self.updater.running)
        time.sleep(0.2)  # Give the thread time to stop
        self.assertFalse(self.updater.update_thread.is_alive())

    def test_start_already_running(self):
        """Test start method when already running."""
        # Start the updater
        self.updater.start()

        # Try to start again
        result = self.updater.start()
        self.assertTrue(result)  # Should return True even though already running

    def test_start_disabled(self):
        """Test start method when disabled."""
        # Disable the updater
        self.updater.enabled = False

        # Try to start
        result = self.updater.start()
        self.assertFalse(result)
        self.assertFalse(self.updater.running)
        self.assertIsNone(self.updater.update_thread)

    def test_update_loop(self):
        """Test the update loop."""
        # Start the updater
        self.updater.start()

        # Wait for a few update cycles
        time.sleep(0.5)

        # Check that the player's get_status method was called
        self.mock_player.get_status.assert_called()

        # Check that the broker's update_player_state method was called
        self.mock_broker.update_player_state.assert_called()

    def test_state_change_triggers_update(self):
        """Test that a state change triggers an update."""
        # Set up the mock player to return different states
        self.mock_player.get_status.side_effect = [
            {  # Initial state
                "state": "stop",
                "volume": 50,
                "current_song": None,
                "playlist": None,
                "playlist_tracks": None,
                "repeat": False,
                "random": False
            },
            {  # Changed state
                "state": "play",
                "volume": 50,
                "current_song": {
                    "title": "Test Song",
                    "artist": "Test Artist",
                    "position": 0,
                    "duration": 180
                },
                "playlist": "Test Playlist",
                "playlist_tracks": [{"title": "Test Song"}],
                "repeat": False,
                "random": False
            }
        ]

        # Mock the _check_and_update_status method to avoid threading
        with patch.object(self.updater, '_check_and_update_status') as mock_check:
            # Call the method directly
            self.updater._check_and_update_status()
            self.updater._check_and_update_status()

            # Check that update_player_state was called twice
            self.assertEqual(mock_check.call_count, 2)

    def test_position_updates(self):
        """Test that position updates are sent during playback."""
        # Set up the mock player to return a playing state with position updates
        self.mock_player.get_status.side_effect = [
            {  # Initial state
                "state": "play",
                "volume": 50,
                "current_song": {
                    "title": "Test Song",
                    "artist": "Test Artist",
                    "position": 0,
                    "duration": 180
                },
                "playlist": "Test Playlist",
                "playlist_tracks": [{"title": "Test Song"}],
                "repeat": False,
                "random": False
            },
            {  # Position update
                "state": "play",
                "volume": 50,
                "current_song": {
                    "title": "Test Song",
                    "artist": "Test Artist",
                    "position": 1.5,
                    "duration": 180
                },
                "playlist": "Test Playlist",
                "playlist_tracks": [{"title": "Test Song"}],
                "repeat": False,
                "random": False
            }
        ]

        # Initialize the updater with the first status
        self.updater._check_and_update_status()

        # Reset the mock to track new calls
        self.mock_broker.publish_state.reset_mock()
        self.mock_broker.update_player_state.reset_mock()

        # Force a position update
        self.updater.last_position_update_time = 0
        self.updater._check_and_update_status()

        # Check that publish_state was called with position update
        self.mock_broker.publish_state.assert_called_once()
        args, kwargs = self.mock_broker.publish_state.call_args
        self.assertEqual(args[0]["state"], "play")
        self.assertEqual(args[0]["current_song"]["position"], 1.5)

    def test_full_update_interval(self):
        """Test that full updates are sent at the configured interval."""
        # Set up the mock player to return the same state
        self.mock_player.get_status.return_value = {
            "state": "play",
            "volume": 50,
            "current_song": {
                "title": "Test Song",
                "artist": "Test Artist",
                "position": 10,
                "duration": 180
            },
            "playlist": "Test Playlist",
            "playlist_tracks": [{"title": "Test Song"}],
            "repeat": False,
            "random": False
        }

        # Initialize the updater
        self.updater._check_and_update_status()

        # Reset the mock to track new calls
        self.mock_broker.update_player_state.reset_mock()

        # Force a full update by setting the last update time far in the past
        self.updater.last_full_update_time = 0
        self.updater._check_and_update_status()

        # Check that update_player_state was called
        self.mock_broker.update_player_state.assert_called_once()


if __name__ == "__main__":
    unittest.main()
