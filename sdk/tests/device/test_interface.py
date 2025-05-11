"""
Tests for the PlayerInterface class.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test directly to avoid importing the entire package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../amora_sdk/device')))
from interface import PlayerInterface
from tests.mocks.mock_player import MockMusicPlayer

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestPlayerInterface(unittest.TestCase):
    """Tests for the PlayerInterface class."""

    def setUp(self):
        """Set up the test case."""
        self.config = {
            "mpd": {
                "host": "localhost",
                "port": 6600
            },
            "content": {
                "storage_path": "/home/user/music",
                "playlists_path": "/home/user/music/playlists"
            },
            "audio": {
                "backend": "pipewire",
                "device": "default",
                "volume": 80
            },
            "dev_mode": True
        }

        # Create a mock player
        self.mock_player = MockMusicPlayer(self.config)

        # Create the interface
        self.interface = PlayerInterface(self.config)

        # Replace the player with our mock
        self.interface.player = self.mock_player

        # Set up the mock player with initial state
        self.mock_player.connected = True
        self.mock_player.state = "playing"
        self.mock_player.volume = 60
        self.mock_player.current_song = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "file": "test.mp3",
            "duration": 180,
            "position": 60
        }
        self.mock_player.current_playlist = "Test Playlist"

    def tearDown(self):
        """Tear down the test case."""
        pass

    def test_connect(self):
        """Test the connect method."""
        # Test successful connection
        result = self.interface.connect()
        self.assertTrue(result)
        self.assertTrue(self.interface.connected)

        # Test connection failure
        self.interface.player.connect = MagicMock(return_value=False)
        result = self.interface.connect()
        self.assertFalse(result)
        self.assertFalse(self.interface.connected)

        # Test exception handling
        self.interface.player.connect = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.connect()
        self.assertFalse(result)
        self.assertFalse(self.interface.connected)

    def test_disconnect(self):
        """Test the disconnect method."""
        # Connect first
        self.interface.connect()
        self.assertTrue(self.interface.connected)

        # Test successful disconnection
        self.interface.disconnect()
        self.assertFalse(self.interface.connected)

        # Test exception handling
        self.interface.player.disconnect = MagicMock(side_effect=Exception("Test exception"))
        self.interface.disconnect()
        self.assertFalse(self.interface.connected)

    def test_play(self):
        """Test the play method."""
        # Test successful play
        result = self.interface.play()
        self.assertTrue(result)
        self.assertEqual(self.interface.player.state, "playing")

        # Test exception handling
        self.interface.player.play = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.play()
        self.assertFalse(result)

    def test_pause(self):
        """Test the pause method."""
        # Play first
        self.interface.play()

        # Test successful pause
        result = self.interface.pause()
        self.assertTrue(result)
        self.assertEqual(self.interface.player.state, "paused")

        # Test exception handling
        self.interface.player.pause = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.pause()
        self.assertFalse(result)

    def test_stop(self):
        """Test the stop method."""
        # Play first
        self.interface.play()

        # Test successful stop
        result = self.interface.stop()
        self.assertTrue(result)
        self.assertEqual(self.interface.player.state, "stopped")

        # Test exception handling
        self.interface.player.stop = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.stop()
        self.assertFalse(result)

    def test_next(self):
        """Test the next method."""
        # Play first
        self.interface.play()

        # Test successful next
        result = self.interface.next()
        self.assertTrue(result)
        self.assertEqual(self.interface.player.current_song["title"], "Next Song")

        # Test exception handling
        self.interface.player.next = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.next()
        self.assertFalse(result)

    def test_previous(self):
        """Test the previous method."""
        # Play first
        self.interface.play()

        # Test successful previous
        result = self.interface.previous()
        self.assertTrue(result)
        self.assertEqual(self.interface.player.current_song["title"], "Previous Song")

        # Test exception handling
        self.interface.player.previous = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.previous()
        self.assertFalse(result)

    def test_set_volume(self):
        """Test the set_volume method."""
        # Test successful set_volume
        result = self.interface.set_volume(75)
        self.assertTrue(result)
        self.assertEqual(self.interface.player.volume, 75)

        # Test exception handling
        self.interface.player.set_volume = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.set_volume(50)
        self.assertFalse(result)

    def test_get_volume(self):
        """Test the get_volume method."""
        # Set volume first
        self.interface.set_volume(60)

        # Test successful get_volume
        volume = self.interface.get_volume()
        self.assertEqual(volume, 60)

        # Test exception handling
        self.interface.player.get_volume = MagicMock(side_effect=Exception("Test exception"))
        volume = self.interface.get_volume()
        self.assertEqual(volume, 0)

    def test_get_status(self):
        """Test the get_status method."""
        # Play first
        self.interface.play()

        # Test successful get_status
        status = self.interface.get_status()
        self.assertEqual(status["state"], "playing")
        self.assertIsNotNone(status["current_song"])

        # Test exception handling
        self.interface.player.get_status = MagicMock(side_effect=Exception("Test exception"))
        status = self.interface.get_status()
        self.assertEqual(status["state"], "unknown")
        self.assertIsNone(status["current_song"])

    def test_get_playlists(self):
        """Test the get_playlists method."""
        # Test successful get_playlists
        playlists = self.interface.get_playlists()
        self.assertEqual(len(playlists), 2)
        self.assertIn("Test Playlist 1", playlists)

        # Test exception handling
        self.interface.player.get_playlists = MagicMock(side_effect=Exception("Test exception"))
        playlists = self.interface.get_playlists()
        self.assertEqual(playlists, [])

    def test_update_database(self):
        """Test the update_database method."""
        # Test successful update_database
        result = self.interface.update_database()
        self.assertTrue(result)

        # Test exception handling
        self.interface.player.update_database = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.update_database()
        self.assertFalse(result)

    def test_play_playlist(self):
        """Test the play_playlist method."""
        # Test successful play_playlist
        result = self.interface.play_playlist("Test Playlist 1")
        self.assertTrue(result)
        self.assertEqual(self.interface.player.current_playlist, "Test Playlist 1")
        self.assertEqual(self.interface.player.state, "playing")

        # Test exception handling
        self.interface.player.play_playlist = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.play_playlist("Test Playlist 2")
        self.assertFalse(result)

    def test_set_repeat(self):
        """Test the set_repeat method."""
        # Test successful set_repeat
        result = self.interface.set_repeat(True)
        self.assertTrue(result)
        self.assertTrue(self.interface.player.repeat)

        # Test exception handling
        self.interface.player.set_repeat = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.set_repeat(False)
        self.assertFalse(result)

    def test_set_random(self):
        """Test the set_random method."""
        # Test successful set_random
        result = self.interface.set_random(True)
        self.assertTrue(result)
        self.assertTrue(self.interface.player.random)

        # Test exception handling
        self.interface.player.set_random = MagicMock(side_effect=Exception("Test exception"))
        result = self.interface.set_random(False)
        self.assertFalse(result)

    def test_status_callbacks(self):
        """Test the status callbacks."""
        # Create a mock callback
        callback = MagicMock()

        # Register the callback
        self.interface.register_status_callback(callback)

        # Create a status update
        status = {"state": "playing", "volume": 75}

        # Notify the callbacks
        self.interface.notify_status_update(status)

        # Check that the callback was called with the status
        callback.assert_called_once_with(status)

        # Test exception handling in callback
        callback.side_effect = Exception("Test exception")
        self.interface.notify_status_update(status)  # Should not raise an exception

if __name__ == '__main__':
    unittest.main()
