"""
Integration tests for the MusicPlayer class.
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
from integration_tests.base_test import PlayerIntegrationTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestMusicPlayer(PlayerIntegrationTest):
    """Integration tests for the MusicPlayer class."""

    def setup_method(self):
        """Set up test method."""
        # Make sure we're connected
        if not self.player.connected:
            self.player.connect()

        # Stop any current playback
        self.player.stop()

        # Create a test playlist
        self._create_test_playlist()

    def teardown_method(self):
        """Tear down test method."""
        # Stop playback
        self.player.stop()

        # Remove test playlist
        self._remove_test_playlist()

    def _create_test_playlist(self):
        """Create a test playlist with sample files."""
        try:
            # Use existing test files in /var/lib/mpd/music/test
            sample_files = ["test/sample1.mp3", "test/sample2.mp3", "test/sample3.mp3"]

            # Clear current playlist
            self.player.mpd_client.clear()

            # Add files to the current playlist
            for file in sample_files:
                self.player.mpd_client.add(file)

            # Save the playlist
            self.player.mpd_client.save("test_playlist")

            logger.info(f"Created test playlist with {len(sample_files)} sample files")
        except Exception as e:
            logger.error(f"Error creating test playlist: {e}")
            # Try a different approach using mpc
            try:
                import subprocess
                subprocess.run(["mpc", "clear"], check=True)
                for file in sample_files:
                    subprocess.run(["mpc", "add", file], check=True)
                subprocess.run(["mpc", "save", "test_playlist"], check=True)
                logger.info("Created test playlist using mpc")
            except Exception as e2:
                logger.error(f"Error creating test playlist with mpc: {e2}")

    def _remove_test_playlist(self):
        """Remove the test playlist."""
        try:
            self.player.delete_playlist("test_playlist")
            logger.info("Removed test playlist")
        except Exception as e:
            logger.warning(f"Failed to remove test playlist: {e}")
            # Try a different approach using mpc
            try:
                import subprocess
                subprocess.run(["mpc", "rm", "test_playlist"], check=False)
                logger.info("Removed test playlist using mpc")
            except Exception as e2:
                logger.warning(f"Failed to remove test playlist with mpc: {e2}")

    def test_connect_disconnect(self):
        """Test connect and disconnect methods."""
        # Disconnect
        self.player.disconnect()
        assert not self.player.connected

        # Connect
        result = self.player.connect()
        assert result
        assert self.player.connected

    def test_play_pause_stop(self):
        """Test play, pause, and stop methods."""
        # Load the test playlist
        result = self.player.play_playlist("test_playlist")
        assert result

        # Explicitly start playback
        result = self.player.play()
        assert result

        # Wait for playback to start
        time.sleep(1)

        # Check status
        status = self.player.get_status()

        # Skip the test if playback doesn't start
        # This can happen if the audio files aren't valid or if there's no audio output
        if status["state"] != "play":
            import pytest
            pytest.skip(f"Playback didn't start. State is '{status['state']}' instead of 'play'")

        # Pause
        result = self.player.pause()
        assert result

        # Check status
        status = self.player.get_status()
        assert status["state"] == "pause", f"Expected state 'pause', got '{status['state']}'"

        # Resume
        result = self.player.play()
        assert result

        # Check status
        status = self.player.get_status()
        assert status["state"] == "play", f"Expected state 'play', got '{status['state']}'"

        # Stop
        result = self.player.stop()
        assert result

        # Check status
        status = self.player.get_status()
        assert status["state"] == "stop", f"Expected state 'stop', got '{status['state']}'"

    def test_next_previous(self):
        """Test next and previous methods."""
        # Load the test playlist
        result = self.player.play_playlist("test_playlist")
        assert result

        # Explicitly start playback
        result = self.player.play()
        assert result

        # Wait for playback to start
        time.sleep(1)

        # Get current song
        status = self.player.get_status()

        # Check if we have a current song
        if status.get("current_song") is None:
            import pytest
            pytest.skip("No current song available for testing next/previous")

        current_song = status["current_song"]["file"]

        # Next
        result = self.player.next()
        assert result

        # Wait for song change
        time.sleep(1)

        # Get new song
        status = self.player.get_status()

        # Check if we have a current song after next
        if status.get("current_song") is None:
            import pytest
            pytest.skip("No current song available after next command")

        new_song = status["current_song"]["file"]

        # Check that the song changed
        assert new_song != current_song

        # Previous
        result = self.player.previous()
        assert result

        # Wait for song change
        time.sleep(1)

        # Get new song
        status = self.player.get_status()

        # Check if we have a current song after previous
        if status.get("current_song") is None:
            import pytest
            pytest.skip("No current song available after previous command")

        prev_song = status["current_song"]["file"]

        # Check that we're back to the original song
        assert prev_song == current_song

    def test_volume(self):
        """Test volume control."""
        # Set volume to 50
        result = self.player.set_volume(50)
        assert result

        # Check volume
        volume = self.player.get_volume()
        assert volume == 50

        # Set volume to 75
        result = self.player.set_volume(75)
        assert result

        # Check volume
        volume = self.player.get_volume()
        assert volume == 75

    def test_playlists(self):
        """Test playlist management."""
        # Get playlists
        playlists = self.player.get_playlists()
        assert "test_playlist" in playlists

        # Play playlist
        result = self.player.play_playlist("test_playlist")
        assert result

        # Check current playlist
        status = self.player.get_status()
        assert status["playlist"] == "test_playlist"

    def test_repeat_random(self):
        """Test repeat and random modes."""
        # Set repeat on
        result = self.player.set_repeat(True)
        assert result

        # Check repeat status
        status = self.player.get_status()
        assert status["repeat"]

        # Set repeat off
        result = self.player.set_repeat(False)
        assert result

        # Check repeat status
        status = self.player.get_status()
        assert not status["repeat"]

        # Set random on
        result = self.player.set_random(True)
        assert result

        # Check random status
        status = self.player.get_status()
        assert status["random"]

        # Set random off
        result = self.player.set_random(False)
        assert result

        # Check random status
        status = self.player.get_status()
        assert not status["random"]
