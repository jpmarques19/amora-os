#!/usr/bin/env python3
"""
Example application demonstrating the new architecture with proper separation of concerns.

This script shows how to use the AmoraApp class to integrate the player and broker modules.
"""

import asyncio
import logging
import sys
import os
import time
import signal
from typing import Dict, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from amora_sdk.device.player import MusicPlayer
from amora_sdk.device.broker.config import BrokerConfig, ConnectionOptions, QoS
from amora_sdk.device.app import AmoraApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_player_config() -> Dict[str, Any]:
    """
    Create player configuration.
    
    Returns:
        Player configuration dictionary
    """
    return {
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


def create_broker_config() -> BrokerConfig:
    """
    Create broker configuration.
    
    Returns:
        BrokerConfig instance
    """
    return BrokerConfig(
        broker_url="localhost",
        port=1883,
        client_id=f"amora-device-{int(time.time())}",
        device_id="amora-player-001",
        topic_prefix="amora/devices",
        connection_options=ConnectionOptions(
            use_tls=False,
            reconnect_on_failure=True
        ),
        default_qos=QoS.AT_LEAST_ONCE,
        raw_config={
            "status_updater": {
                "enabled": True,
                "update_interval": 1.0,
                "position_update_interval": 1.0,
                "full_update_interval": 5.0
            }
        }
    )


def create_app_config() -> Dict[str, Any]:
    """
    Create application configuration.
    
    Returns:
        Application configuration dictionary
    """
    return {
        "status_updater": {
            "enabled": True,
            "update_interval": 1.0,
            "position_update_interval": 1.0,
            "full_update_interval": 5.0
        }
    }


async def main():
    """Main application entry point."""
    # Create player
    player_config = create_player_config()
    player = MusicPlayer(player_config)
    
    # Connect to player
    if not player.connect():
        logger.error("Failed to connect to player")
        return
    
    # Create broker config
    broker_config = create_broker_config()
    
    # Create app config
    app_config = create_app_config()
    
    # Create app
    app = AmoraApp(player, broker_config, app_config)
    
    # Connect to services
    if not app.connect():
        logger.error("Failed to connect to services")
        player.disconnect()
        return
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        app.disconnect()
        player.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Application started. Press Ctrl+C to exit.")
    
    # Keep the application running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        # Clean up
        app.disconnect()
        player.disconnect()
        logger.info("Application stopped")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
