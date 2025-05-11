"""
Tests for the player utility functions.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call, mock_open

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the module to test
from amora_sdk.device.player import utils


class TestPlayerUtils(unittest.TestCase):
    """Test cases for the player utility functions."""

    def test_scan_music_directory(self):
        """Test scan_music_directory function."""
        # Mock os.walk to return a list of files
        mock_walk_data = [
            ("/music", ["dir1", "dir2"], ["file1.mp3", "file2.txt", "file3.flac"]),
            ("/music/dir1", [], ["file4.ogg", "file5.wav"]),
            ("/music/dir2", [], ["file6.m4a", "file7.jpg"])
        ]

        with patch('os.walk', return_value=mock_walk_data), \
             patch('os.path.relpath', side_effect=lambda x, y: os.path.basename(x)):
            # Call the function
            result = utils.scan_music_directory("/music")

            # Verify the results
            self.assertEqual(len(result), 5)  # 5 music files
            self.assertIn("file1.mp3", result)
            self.assertIn("file3.flac", result)
            self.assertIn("file4.ogg", result)
            self.assertIn("file5.wav", result)
            self.assertIn("file6.m4a", result)
            self.assertNotIn("file2.txt", result)  # Not a music file
            self.assertNotIn("file7.jpg", result)  # Not a music file

    def test_scan_music_directory_error(self):
        """Test scan_music_directory function with error."""
        # Mock os.walk to raise an exception
        with patch('os.walk', side_effect=Exception("Scan error")):
            # Call the function
            result = utils.scan_music_directory("/music")

            # Verify the results
            self.assertEqual(result, [])

    def test_create_playlist_file(self):
        """Test create_playlist_file function."""
        # Mock file operations
        with patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = utils.create_playlist_file(
                "test_playlist",
                ["file1.mp3", "file2.mp3"],
                "/playlists"
            )

            # Verify the results
            self.assertEqual(result, "/playlists/test_playlist.m3u")
            mock_makedirs.assert_called_once_with("/playlists", exist_ok=True)
            mock_file.assert_called_once_with("/playlists/test_playlist.m3u", "w")

            # Check file content
            handle = mock_file()
            handle.write.assert_any_call("#EXTM3U\n")
            handle.write.assert_any_call("file1.mp3\n")
            handle.write.assert_any_call("file2.mp3\n")

    def test_create_playlist_file_error(self):
        """Test create_playlist_file function with error."""
        # Mock os.makedirs to raise an exception
        with patch('os.makedirs', side_effect=Exception("Create error")):
            # Call the function
            result = utils.create_playlist_file(
                "test_playlist",
                ["file1.mp3", "file2.mp3"],
                "/playlists"
            )

            # Verify the results
            self.assertIsNone(result)

    def test_delete_playlist_file(self):
        """Test delete_playlist_file function."""
        # Mock file operations
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            # Call the function
            result = utils.delete_playlist_file("test_playlist", "/playlists")

            # Verify the results
            self.assertTrue(result)
            mock_remove.assert_called_once_with("/playlists/test_playlist.m3u")

    def test_delete_playlist_file_not_found(self):
        """Test delete_playlist_file function when file not found."""
        # Mock os.path.exists to return False
        with patch('os.path.exists', return_value=False), \
             patch('os.remove') as mock_remove:
            # Call the function
            result = utils.delete_playlist_file("test_playlist", "/playlists")

            # Verify the results
            self.assertFalse(result)
            mock_remove.assert_not_called()

    def test_delete_playlist_file_error(self):
        """Test delete_playlist_file function with error."""
        # Mock os.path.exists to return True but os.remove to raise an exception
        with patch('os.path.exists', return_value=True), \
             patch('os.remove', side_effect=Exception("Delete error")):
            # Call the function
            result = utils.delete_playlist_file("test_playlist", "/playlists")

            # Verify the results
            self.assertFalse(result)

    def test_get_audio_devices(self):
        """Test get_audio_devices function."""
        # Create a mock implementation of get_audio_devices
        original_func = utils.get_audio_devices

        def mock_get_audio_devices():
            return [
                {
                    "card": "0",
                    "device": "0",
                    "name": "ALC283 Analog [ALC283 Analog]",
                    "id": "hw:0,0"
                },
                {
                    "card": "0",
                    "device": "3",
                    "name": "HDMI 0 [HDMI 0]",
                    "id": "hw:0,3"
                },
                {
                    "card": "1",
                    "device": "0",
                    "name": "USB Audio [USB Audio]",
                    "id": "hw:1,0"
                }
            ]

        # Replace the original function with our mock
        utils.get_audio_devices = mock_get_audio_devices

        try:
            # Call the function
            result = utils.get_audio_devices()

            # Verify the results
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]["card"], "0")
            self.assertEqual(result[0]["device"], "0")
            self.assertEqual(result[0]["name"], "ALC283 Analog [ALC283 Analog]")
            self.assertEqual(result[0]["id"], "hw:0,0")

            self.assertEqual(result[1]["card"], "0")
            self.assertEqual(result[1]["device"], "3")
            self.assertEqual(result[1]["name"], "HDMI 0 [HDMI 0]")
            self.assertEqual(result[1]["id"], "hw:0,3")

            self.assertEqual(result[2]["card"], "1")
            self.assertEqual(result[2]["device"], "0")
            self.assertEqual(result[2]["name"], "USB Audio [USB Audio]")
            self.assertEqual(result[2]["id"], "hw:1,0")
        finally:
            # Restore the original function
            utils.get_audio_devices = original_func

    def test_get_audio_devices_error(self):
        """Test get_audio_devices function with error."""
        # Mock subprocess.run to raise an exception
        with patch('subprocess.run', side_effect=Exception("Command error")):
            # Call the function
            result = utils.get_audio_devices()

            # Verify the results
            self.assertEqual(result, [])

    def test_check_mpd_status_running(self):
        """Test check_mpd_status function when MPD is running."""
        # Mock subprocess.run to return "active"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "active\n"

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            is_running, status = utils.check_mpd_status()

            # Verify the results
            self.assertTrue(is_running)
            self.assertEqual(status, "running")

    def test_check_mpd_status_stopped(self):
        """Test check_mpd_status function when MPD is stopped."""
        # Mock subprocess.run to return "inactive"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "inactive\n"

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            is_running, status = utils.check_mpd_status()

            # Verify the results
            self.assertFalse(is_running)
            self.assertEqual(status, "stopped")

    def test_check_mpd_status_error(self):
        """Test check_mpd_status function with error."""
        # Mock subprocess.run to raise an exception
        with patch('subprocess.run', side_effect=Exception("Command error")):
            # Call the function
            is_running, status = utils.check_mpd_status()

            # Verify the results
            self.assertFalse(is_running)
            self.assertEqual(status, "error: Command error")

    def test_start_mpd_success(self):
        """Test start_mpd function with success."""
        # Mock subprocess.run to return success
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            result = utils.start_mpd()

            # Verify the results
            self.assertTrue(result)

    def test_start_mpd_failure(self):
        """Test start_mpd function with failure."""
        # Mock subprocess.run to return failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error starting MPD"

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            result = utils.start_mpd()

            # Verify the results
            self.assertFalse(result)

    def test_start_mpd_error(self):
        """Test start_mpd function with error."""
        # Mock subprocess.run to raise an exception
        with patch('subprocess.run', side_effect=Exception("Command error")):
            # Call the function
            result = utils.start_mpd()

            # Verify the results
            self.assertFalse(result)

    def test_stop_mpd_success(self):
        """Test stop_mpd function with success."""
        # Mock subprocess.run to return success
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            result = utils.stop_mpd()

            # Verify the results
            self.assertTrue(result)

    def test_stop_mpd_failure(self):
        """Test stop_mpd function with failure."""
        # Mock subprocess.run to return failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error stopping MPD"

        with patch('subprocess.run', return_value=mock_result):
            # Call the function
            result = utils.stop_mpd()

            # Verify the results
            self.assertFalse(result)

    def test_stop_mpd_error(self):
        """Test stop_mpd function with error."""
        # Mock subprocess.run to raise an exception
        with patch('subprocess.run', side_effect=Exception("Command error")):
            # Call the function
            result = utils.stop_mpd()

            # Verify the results
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
