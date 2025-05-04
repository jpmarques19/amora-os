#!/usr/bin/env python3
"""
Main module for the Python Waybox application.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from typing import Dict, Any, Optional

import click
from pydantic import BaseModel, Field

from src.player import MusicPlayer
from src.utils import (
    get_audio_devices,
    get_iquadio_device,
    get_pipewire_devices,
    is_pipewire_running,
    start_pipewire,
    configure_pipewire_for_dev_mode,
    setup_audio_device,
    test_audio_device
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeviceConfig(BaseModel):
    id: str = "waybox-player"
    name: str = "Waybox Player"


class MpdConfig(BaseModel):
    host: str = "localhost"
    port: int = 6600


class ContentConfig(BaseModel):
    storage_path: str = "/home/user/music"
    playlists_path: str = "/home/user/music/playlists"


class AudioConfig(BaseModel):
    backend: str = "pipewire"
    device: str = "default"
    volume: int = Field(default=80, ge=0, le=100)


class WayboxConfig(BaseModel):
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    mpd: MpdConfig = Field(default_factory=MpdConfig)
    content: ContentConfig = Field(default_factory=ContentConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    dev_mode: bool = False


def load_config(config_path: Optional[str] = None) -> WayboxConfig:
    """
    Load configuration from file.

    Args:
        config_path (str, optional): Path to configuration file

    Returns:
        WayboxConfig: Configuration object
    """
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = json.load(f)
                return WayboxConfig(**config_data)
        else:
            logger.warning(f"Configuration file not found: {config_path}")
            return WayboxConfig()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return WayboxConfig()


async def status_update_loop(player: MusicPlayer, interval: int = 5) -> None:
    """
    Periodically update and log player status.

    Args:
        player (MusicPlayer): Music player instance
        interval (int, optional): Update interval in seconds
    """
    while True:
        status = player.get_status()
        logger.debug(f"Player status: {status}")

        # Log current song if playing
        if status["state"] == "play" and status["current_song"]:
            song = status["current_song"]
            logger.info(f"Now playing: {song['title']} - {song['artist']}")

        await asyncio.sleep(interval)


def setup_signal_handlers(player: MusicPlayer) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Args:
        player (MusicPlayer): Music player instance
    """
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        player.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_player(config: WayboxConfig) -> int:
    """
    Run the music player.

    Args:
        config (WayboxConfig): Configuration object

    Returns:
        int: Exit code
    """
    logger.info(f"Starting Python Waybox Player (dev_mode: {config.dev_mode})")

    # Check if MPD is already running and working
    try:
        import subprocess
        result = subprocess.run(['mpc', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("MPD is already running and configured. Skipping audio device setup.")
            skip_audio_setup = True
        else:
            skip_audio_setup = False
    except Exception:
        logger.info("Could not check MPD status, will attempt audio device setup.")
        skip_audio_setup = False

    # Only attempt to configure audio if we didn't detect a working MPD instance
    if not skip_audio_setup:
        # Check if Pipewire is running
        if not is_pipewire_running():
            logger.info("Starting Pipewire...")
            start_pipewire()  # We'll continue even if this fails

        # Configure Pipewire for development mode if needed
        if config.dev_mode:
            logger.info("Configuring Pipewire for development mode...")
            if not configure_pipewire_for_dev_mode():
                logger.warning("Failed to configure Pipewire for development mode")

        # List audio devices
        logger.info("Available audio devices:")
        devices = get_audio_devices()
        for device in devices:
            logger.info(device)

        # List Pipewire devices
        logger.info("Available Pipewire devices:")
        pw_devices = get_pipewire_devices()
        for device in pw_devices:
            logger.info(device)

        # Find IQUADIO DAC
        iquadio_device = get_iquadio_device()
        if iquadio_device:
            logger.info(f"Found IQUADIO DAC at {iquadio_device}")

            # Set up audio device
            if not config.dev_mode:
                logger.info(f"Setting up IQUADIO DAC as default audio device...")
                if not setup_audio_device(iquadio_device):
                    logger.warning("Failed to set up IQUADIO DAC as default audio device")

            # Test IQUADIO DAC
            logger.info(f"Testing IQUADIO DAC...")
            if test_audio_device(iquadio_device):
                logger.info("IQUADIO DAC test successful!")
            else:
                logger.error("IQUADIO DAC test failed!")
        else:
            logger.warning("IQUADIO DAC not found, using default audio device")

    # Initialize music player
    player = MusicPlayer(config.model_dump())

    # Set up signal handlers
    setup_signal_handlers(player)

    # Connect to MPD
    if not player.connect():
        logger.error("Failed to connect to MPD. Exiting.")
        return 1

    # Set initial volume
    player.set_volume(config.audio.volume)

    # Start status update loop
    status_task = asyncio.create_task(status_update_loop(player))

    try:
        # Keep the application running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Application cancelled")
    finally:
        # Clean up
        status_task.cancel()
        player.disconnect()

    return 0


@click.group()
def cli():
    """Python Waybox Player with Pipewire backend."""
    pass


@cli.command()
@click.option("--config", help="Path to configuration file")
@click.option("--dev", is_flag=True, help="Enable development mode")
def start(config, dev):
    """Start the Waybox Player."""
    # Load configuration
    config_obj = load_config(config)

    # Override dev_mode from command line
    if dev:
        config_obj.dev_mode = True

    try:
        exit_code = asyncio.run(run_player(config_obj))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        sys.exit(0)


@cli.command()
@click.option("--device", default="hw:2,0", help="Audio device to test")
def test_audio(device):
    """Test audio output."""
    logger.info(f"Testing audio device: {device}")
    if test_audio_device(device):
        logger.info("Audio test successful!")
        sys.exit(0)
    else:
        logger.error("Audio test failed!")
        sys.exit(1)


def cli_main():
    """Entry point for the CLI."""
    cli()


async def main() -> int:
    """
    Main entry point for the application.

    Returns:
        int: Exit code
    """
    # Load configuration
    config = load_config()

    # Run the player
    return await run_player(config)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        sys.exit(0)
