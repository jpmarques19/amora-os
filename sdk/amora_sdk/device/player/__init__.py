"""
Player module for AmoraSDK Device.

This module provides the music player implementation for Amora OS.
It includes classes for controlling playback and sending real-time status updates.
"""

from .music_player import MusicPlayer
from .status_updater import PlayerStatusUpdater

__all__ = ["MusicPlayer", "PlayerStatusUpdater"]
