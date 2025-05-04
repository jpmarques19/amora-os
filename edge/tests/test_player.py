#!/usr/bin/env python3
"""
Tests for the MusicPlayer class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module, not the class, so we can patch it properly
import player


class TestMusicPlayer(unittest.TestCase):
    """Test cases for the Music Player."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "content": {
                "storage_path": "/home/user/music",
                "playlists_path": "/home/user/music/playlists",
                "default_playlist": "default"
            },
            "audio": {
                "backend": "pipewire",
                "device": "default",
                "volume": 80
            },
            "mpd": {
                "host": "localhost",
                "port": 6600
            },
            "dev_mode": True
        }

        # Create mock MPD client
        self.mock_mpd_client = MagicMock()

        # Create the MPD client patcher
        self.mpd_patcher = patch('mpd.MPDClient', return_value=self.mock_mpd_client)
        self.mock_mpd_class = self.mpd_patcher.start()

        # Create the player instance
        self.player = player.MusicPlayer(self.config)

        # Set the player as connected and set the mock client
        self.player.mpd_client = self.mock_mpd_client
        self.player.connected = True

    def tearDown(self):
        """Clean up after tests."""
        self.mpd_patcher.stop()

    def test_init(self):
        """Test initialization."""
        test_player = player.MusicPlayer(self.config)
        self.assertEqual(test_player.mpd_host, "localhost")
        self.assertEqual(test_player.mpd_port, 6600)
        self.assertEqual(test_player.music_dir, "/home/user/music")
        self.assertEqual(test_player.playlists_dir, "/home/user/music/playlists")
        self.assertEqual(test_player.dev_mode, True)
        self.assertFalse(test_player.connected)
        self.assertIsNone(test_player.current_playlist)

    def test_connect_success(self):
        """Test successful connection."""
        # Reset the player's connection state
        self.player.connected = False

        # Configure the mock
        self.mock_mpd_client.connect.side_effect = None

        # Call the method
        result = self.player.connect()

        # Verify the results
        self.assertTrue(result)
        self.assertTrue(self.player.connected)
        self.mock_mpd_client.connect.assert_called_once_with("localhost", 6600)

    def test_connect_failure(self):
        """Test failed connection."""
        # Reset the player's connection state
        self.player.connected = False

        # Configure the mock to raise an exception
        self.mock_mpd_client.connect.side_effect = Exception("Connection failed")

        # Call the method
        result = self.player.connect()

        # Verify the results
        self.assertFalse(result)
        self.assertFalse(self.player.connected)

    def test_disconnect(self):
        """Test disconnect method."""
        # Ensure the player is connected
        self.player.connected = True

        # Call the method
        self.player.disconnect()

        # Verify the results
        self.mock_mpd_client.close.assert_called_once()
        self.mock_mpd_client.disconnect.assert_called_once()
        self.assertFalse(self.player.connected)

    def test_disconnect_error(self):
        """Test disconnect with error."""
        # Ensure the player is connected
        self.player.connected = True

        # Configure the mock to raise an exception
        self.mock_mpd_client.close.side_effect = Exception("Disconnect error")

        # Call the method
        self.player.disconnect()

        # Verify the results
        self.assertFalse(self.player.connected)

    def test_ensure_connected_already_connected(self):
        """Test _ensure_connected when already connected."""
        # Ensure the player is connected
        self.player.connected = True

        # Configure the mock
        self.mock_mpd_client.ping.return_value = None

        # Call the method
        result = self.player._ensure_connected()

        # Verify the results
        self.assertTrue(result)
        self.mock_mpd_client.ping.assert_called_once()

    def test_ensure_connected_reconnect(self):
        """Test _ensure_connected when reconnection needed."""
        # Ensure the player is connected
        self.player.connected = True

        # Configure the mock to raise an exception
        self.mock_mpd_client.ping.side_effect = Exception("Connection lost")

        # Mock the connect method
        with patch.object(self.player, 'connect', return_value=True) as mock_connect:
            # Call the method
            result = self.player._ensure_connected()

            # Verify the results
            self.assertTrue(result)
            mock_connect.assert_called_once()

    def test_ensure_connected_not_connected(self):
        """Test _ensure_connected when not connected."""
        # Ensure the player is not connected
        self.player.connected = False

        # Mock the connect method
        with patch.object(self.player, 'connect', return_value=True) as mock_connect:
            # Call the method
            result = self.player._ensure_connected()

            # Verify the results
            self.assertTrue(result)
            mock_connect.assert_called_once()

    def test_play(self):
        """Test play method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.play()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.play.assert_called_once()

    def test_play_not_connected(self):
        """Test play method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.play()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.play.assert_not_called()

    def test_play_error(self):
        """Test play method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.play.side_effect = Exception("Play error")

            # Call the method
            result = self.player.play()

            # Verify the results
            self.assertFalse(result)

    def test_pause(self):
        """Test pause method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.pause()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.pause.assert_called_once_with(1)

    def test_pause_not_connected(self):
        """Test pause method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.pause()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.pause.assert_not_called()

    def test_pause_error(self):
        """Test pause method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.pause.side_effect = Exception("Pause error")

            # Call the method
            result = self.player.pause()

            # Verify the results
            self.assertFalse(result)

    def test_stop(self):
        """Test stop method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.stop()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.stop.assert_called_once()

    def test_stop_not_connected(self):
        """Test stop method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.stop()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.stop.assert_not_called()

    def test_stop_error(self):
        """Test stop method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.stop.side_effect = Exception("Stop error")

            # Call the method
            result = self.player.stop()

            # Verify the results
            self.assertFalse(result)

    def test_next(self):
        """Test next method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.next()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.next.assert_called_once()

    def test_next_not_connected(self):
        """Test next method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.next()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.next.assert_not_called()

    def test_next_error(self):
        """Test next method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.next.side_effect = Exception("Next error")

            # Call the method
            result = self.player.next()

            # Verify the results
            self.assertFalse(result)

    def test_previous(self):
        """Test previous method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.previous()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.previous.assert_called_once()

    def test_previous_not_connected(self):
        """Test previous method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.previous()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.previous.assert_not_called()

    def test_previous_error(self):
        """Test previous method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.previous.side_effect = Exception("Previous error")

            # Call the method
            result = self.player.previous()

            # Verify the results
            self.assertFalse(result)

    def test_set_volume(self):
        """Test set_volume method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.set_volume(75)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.setvol.assert_called_once_with(75)

    def test_set_volume_not_connected(self):
        """Test set_volume method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.set_volume(75)

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.setvol.assert_not_called()

    def test_set_volume_error(self):
        """Test set_volume method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.setvol.side_effect = Exception("Set volume error")

            # Call the method
            result = self.player.set_volume(75)

            # Verify the results
            self.assertFalse(result)

    def test_set_volume_limits(self):
        """Test set_volume method with out-of-range values."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method with a value below the minimum
            result = self.player.set_volume(-10)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.setvol.assert_called_once_with(0)

            # Reset the mock
            self.mock_mpd_client.reset_mock()

            # Call the method with a value above the maximum
            result = self.player.set_volume(110)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.setvol.assert_called_once_with(100)

    def test_get_volume(self):
        """Test get_volume method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock
            self.mock_mpd_client.status.return_value = {"volume": "75"}

            # Call the method
            volume = self.player.get_volume()

            # Verify the results
            self.assertEqual(volume, 75)
            self.mock_mpd_client.status.assert_called_once()

    def test_get_volume_not_connected(self):
        """Test get_volume method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            volume = self.player.get_volume()

            # Verify the results
            self.assertEqual(volume, 0)
            self.mock_mpd_client.status.assert_not_called()

    def test_get_volume_error(self):
        """Test get_volume method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.status.side_effect = Exception("Get volume error")

            # Call the method
            volume = self.player.get_volume()

            # Verify the results
            self.assertEqual(volume, 0)

    def test_get_status(self):
        """Test get_status method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mocks
            self.mock_mpd_client.status.return_value = {
                "state": "play",
                "volume": "75",
                "elapsed": "30.5"
            }
            self.mock_mpd_client.currentsong.return_value = {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "file": "test.mp3",
                "duration": "180"
            }

            # Call the method
            status = self.player.get_status()

            # Verify the results
            self.assertEqual(status["state"], "play")
            self.assertEqual(status["volume"], 75)
            self.assertEqual(status["current_song"]["title"], "Test Song")
            self.assertEqual(status["current_song"]["artist"], "Test Artist")
            self.assertEqual(status["current_song"]["duration"], 180)
            self.assertEqual(status["current_song"]["position"], 30)
            self.mock_mpd_client.status.assert_called_once()
            self.mock_mpd_client.currentsong.assert_called_once()

    def test_get_status_not_connected(self):
        """Test get_status method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            status = self.player.get_status()

            # Verify the results
            self.assertEqual(status["state"], "stopped")
            self.assertEqual(status["volume"], 0)
            self.assertIsNone(status["current_song"])
            self.mock_mpd_client.status.assert_not_called()
            self.mock_mpd_client.currentsong.assert_not_called()

    def test_get_status_error(self):
        """Test get_status method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.status.side_effect = Exception("Get status error")

            # Call the method
            status = self.player.get_status()

            # Verify the results
            self.assertEqual(status["state"], "stopped")
            self.assertEqual(status["volume"], 0)
            self.assertIsNone(status["current_song"])

    def test_update_database(self):
        """Test update_database method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.update_database()

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.update.assert_called_once()

    def test_update_database_not_connected(self):
        """Test update_database method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.update_database()

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.update.assert_not_called()

    def test_update_database_error(self):
        """Test update_database method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.update.side_effect = Exception("Update database error")

            # Call the method
            result = self.player.update_database()

            # Verify the results
            self.assertFalse(result)

    def test_get_playlists(self):
        """Test get_playlists method."""
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=["playlist1", "playlist2"]), \
             patch('os.path.isdir', return_value=True):
            playlists = self.player.get_playlists()
            self.assertEqual(playlists, ["playlist1", "playlist2"])

    def test_get_playlists_no_directory(self):
        """Test get_playlists method when directory doesn't exist."""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs:
            playlists = self.player.get_playlists()
            self.assertEqual(playlists, [])
            mock_makedirs.assert_called_once_with(self.player.playlists_dir, exist_ok=True)

    def test_create_playlist(self):
        """Test create_playlist method."""
        # Use a context manager to ensure all mocks are properly cleaned up
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('json.dump') as mock_json_dump:
            # Call the method
            result = self.player.create_playlist("test_playlist")

            # Verify the results
            self.assertTrue(result)
            mock_makedirs.assert_called_once_with(os.path.join(self.player.playlists_dir, "test_playlist"), exist_ok=True)
            mock_json_dump.assert_called_once()

    def test_create_playlist_error(self):
        """Test create_playlist method with error."""
        with patch('os.path.exists', side_effect=Exception("Create playlist error")):
            result = self.player.create_playlist("test_playlist")
            self.assertFalse(result)

    def test_play_playlist(self):
        """Test play_playlist method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('os.walk', return_value=[
                 ("/path/to/playlist", [], ["song1.mp3", "song2.mp3", "metadata.json"])
             ]), \
             patch('os.path.relpath', side_effect=lambda x, y: os.path.basename(x)):
            # Call the method
            result = self.player.play_playlist("test_playlist")

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.stop.assert_called_once()
            self.mock_mpd_client.clear.assert_called_once()
            self.assertEqual(self.mock_mpd_client.add.call_count, 2)  # Two songs added
            self.mock_mpd_client.play.assert_called_once()
            self.assertEqual(self.player.current_playlist, "test_playlist")

    def test_play_playlist_not_found(self):
        """Test play_playlist method when playlist not found."""
        with patch('os.path.exists', return_value=False):
            # Call the method
            result = self.player.play_playlist("test_playlist")

            # Verify the results
            self.assertFalse(result)

    def test_play_playlist_not_connected(self):
        """Test play_playlist method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.play_playlist("test_playlist")

            # Verify the results
            self.assertFalse(result)

    def test_play_playlist_error(self):
        """Test play_playlist method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True), \
             patch('os.path.exists', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.stop.side_effect = Exception("Play playlist error")

            # Call the method
            result = self.player.play_playlist("test_playlist")

            # Verify the results
            self.assertFalse(result)

    def test_set_crossfade(self):
        """Test set_crossfade method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method
            result = self.player.set_crossfade(5)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.crossfade.assert_called_once_with(5)

    def test_set_crossfade_not_connected(self):
        """Test set_crossfade method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.set_crossfade(5)

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.crossfade.assert_not_called()

    def test_set_crossfade_error(self):
        """Test set_crossfade method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.crossfade.side_effect = Exception("Set crossfade error")

            # Call the method
            result = self.player.set_crossfade(5)

            # Verify the results
            self.assertFalse(result)

    def test_set_repeat(self):
        """Test set_repeat method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method with True
            result = self.player.set_repeat(True)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.repeat.assert_called_once_with(1)

            # Reset the mock
            self.mock_mpd_client.reset_mock()

            # Call the method with False
            result = self.player.set_repeat(False)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.repeat.assert_called_once_with(0)

    def test_set_repeat_not_connected(self):
        """Test set_repeat method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.set_repeat(True)

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.repeat.assert_not_called()

    def test_set_repeat_error(self):
        """Test set_repeat method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.repeat.side_effect = Exception("Set repeat error")

            # Call the method
            result = self.player.set_repeat(True)

            # Verify the results
            self.assertFalse(result)

    def test_set_random(self):
        """Test set_random method."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Call the method with True
            result = self.player.set_random(True)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.random.assert_called_once_with(1)

            # Reset the mock
            self.mock_mpd_client.reset_mock()

            # Call the method with False
            result = self.player.set_random(False)

            # Verify the results
            self.assertTrue(result)
            self.mock_mpd_client.random.assert_called_once_with(0)

    def test_set_random_not_connected(self):
        """Test set_random method when not connected."""
        # Mock _ensure_connected to return False
        with patch.object(self.player, '_ensure_connected', return_value=False):
            # Call the method
            result = self.player.set_random(True)

            # Verify the results
            self.assertFalse(result)
            self.mock_mpd_client.random.assert_not_called()

    def test_set_random_error(self):
        """Test set_random method with error."""
        # Mock _ensure_connected to return True
        with patch.object(self.player, '_ensure_connected', return_value=True):
            # Configure the mock to raise an exception
            self.mock_mpd_client.random.side_effect = Exception("Set random error")

            # Call the method
            result = self.player.set_random(True)

            # Verify the results
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
