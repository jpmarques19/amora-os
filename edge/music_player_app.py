#!/usr/bin/env python3
"""
Amora Music Player Application

This application integrates the Amora SDK player and broker modules
using a procedural approach rather than an object-oriented one.
"""

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the SDK to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../sdk')))

# Import SDK components
from amora_sdk.device.player import MusicPlayer
from amora_sdk.device.broker.manager import BrokerManager
from amora_sdk.device.broker.config import BrokerConfig, ConnectionOptions, QoS
from amora_sdk.device.broker.messages import CommandMessage, ResponseMessage

# Global variables
player = None
broker = None
running = False
update_thread = None
last_status = None
last_full_update_time = 0
last_position_update_time = 0

# Configuration
update_interval = 1.0  # seconds
position_update_interval = 1.0  # seconds
full_update_interval = 5.0  # seconds
enable_status_updates = True


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


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load application configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # For now, return a default configuration
    # In a real application, this would load from a file
    return {
        "status_updater": {
            "enabled": True,
            "update_interval": 1.0,
            "position_update_interval": 1.0,
            "full_update_interval": 5.0
        }
    }


def update_player_state() -> bool:
    """
    Update the player state.
    
    This function gets the current state from the player and
    publishes it to the broker.
    
    Returns:
        True if update was successful, False otherwise
    """
    global player, broker
    
    try:
        # Get the current state from the player
        state = player.get_status()
        
        # Publish the state
        return broker.publish_state(state)
    except Exception as e:
        logger.error(f"Error updating player state: {e}")
        return False


def check_and_update_status() -> None:
    """Check player status and publish updates if needed."""
    global player, broker, last_status, last_full_update_time, last_position_update_time
    
    current_time = time.time()
    
    # Get current status
    current_status = player.get_status()
    
    # Determine if we need to send an update
    send_update = False
    send_full_update = False
    
    # Always send a full update periodically
    if current_time - last_full_update_time >= full_update_interval:
        send_update = True
        send_full_update = True
        last_full_update_time = current_time
    
    # Send position updates more frequently when playing
    elif (current_status.get("state") == "play" and 
          current_time - last_position_update_time >= position_update_interval):
        send_update = True
        last_position_update_time = current_time
    
    # Check for state changes
    elif last_status is not None:
        # Check if playback state changed
        if current_status.get("state") != last_status.get("state"):
            send_update = True
            send_full_update = True
        
        # Check if current song changed
        elif (current_status.get("current_song") is not None and 
              last_status.get("current_song") is not None and
              current_status.get("current_song").get("file") != 
              last_status.get("current_song").get("file")):
            send_update = True
            send_full_update = True
        
        # Check if volume changed
        elif current_status.get("volume") != last_status.get("volume"):
            send_update = True
        
        # Check if repeat or random changed
        elif (current_status.get("repeat") != last_status.get("repeat") or
              current_status.get("random") != last_status.get("random")):
            send_update = True
    else:
        # First update
        send_update = True
        send_full_update = True
    
    # Send the update if needed
    if send_update:
        if send_full_update:
            # Send full status update
            update_player_state()
        else:
            # For position updates, we can optimize by only sending the position
            if current_status.get("state") == "play" and current_status.get("current_song"):
                position_update = {
                    "state": current_status.get("state"),
                    "current_song": {
                        "position": current_status.get("current_song", {}).get("position", 0)
                    }
                }
                broker.publish_state(position_update)
            else:
                # For other changes, send the full update
                update_player_state()
    
    # Update last status
    last_status = current_status


def status_update_loop() -> None:
    """Main status update loop."""
    global running
    
    while running:
        try:
            check_and_update_status()
        except Exception as e:
            logger.error(f"Error in status update loop: {e}")
        
        # Sleep for the update interval
        time.sleep(update_interval)


def start_status_updates() -> bool:
    """
    Start status updates.
    
    Returns:
        True if started successfully, False otherwise
    """
    global running, update_thread
    
    if running:
        logger.warning("Status updates already running")
        return True
    
    if not enable_status_updates:
        logger.info("Status updates are disabled in configuration")
        return False
    
    running = True
    update_thread = threading.Thread(target=status_update_loop, daemon=True)
    update_thread.start()
    logger.info("Player status updates started")
    return True


def stop_status_updates() -> None:
    """Stop status updates."""
    global running, update_thread
    
    running = False
    if update_thread and update_thread.is_alive():
        update_thread.join(timeout=2.0)
    logger.info("Player status updates stopped")


def create_command_handler(command: str):
    """
    Create a command handler for a player method.
    
    Args:
        command: Command name
        
    Returns:
        Command handler function
    """
    def handler(command_msg: CommandMessage) -> ResponseMessage:
        try:
            # Get the method from the player interface
            method = getattr(player, command, None)
            if method and callable(method):
                # Call the method with parameters
                params = command_msg.params or {}
                result = method(**params)
                
                # Create response
                response = ResponseMessage(
                    command_id=command_msg.command_id,
                    result=True if result is not False else False,
                    message=f"Command {command} executed",
                    data={"result": result}
                )
                
                # Update player state after command execution
                update_player_state()
                
                return response
            else:
                logger.warning(f"Command {command} not found in player interface")
                return ResponseMessage(
                    command_id=command_msg.command_id,
                    result=False,
                    message=f"Command {command} not supported"
                )
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return ResponseMessage(
                command_id=command_msg.command_id,
                result=False,
                message=f"Error executing command: {str(e)}"
            )
    
    return handler


def on_command_received(command_msg: CommandMessage) -> None:
    """
    Handle received command.
    
    Args:
        command_msg: Command message
    """
    logger.debug(f"Command received: {command_msg.command}")
    # The actual command execution is handled by the registered command handlers


def register_command_handlers() -> None:
    """Register command handlers for standard player commands."""
    global broker
    
    # Register handlers for standard player commands
    standard_commands = [
        "play", "pause", "stop", "next", "previous", 
        "set_volume", "get_volume", "get_status", "get_playlists",
        "play_playlist", "set_repeat", "set_random", 
        "create_playlist", "delete_playlist", "get_playlist_songs",
        "update_database"
    ]
    
    for command in standard_commands:
        broker.register_command_handler(command, create_command_handler(command))


def initialize(config: Dict[str, Any]) -> bool:
    """
    Initialize the application.
    
    Args:
        config: Application configuration
        
    Returns:
        True if initialization was successful, False otherwise
    """
    global player, broker, update_interval, position_update_interval, full_update_interval, enable_status_updates
    
    # Update configuration
    update_interval = config.get("status_updater", {}).get("update_interval", 1.0)
    position_update_interval = config.get("status_updater", {}).get("position_update_interval", 1.0)
    full_update_interval = config.get("status_updater", {}).get("full_update_interval", 5.0)
    enable_status_updates = config.get("status_updater", {}).get("enabled", True)
    
    try:
        # Create player
        player_config = create_player_config()
        player = MusicPlayer(player_config)
        
        # Connect to player
        if not player.connect():
            logger.error("Failed to connect to player")
            return False
        
        # Create broker
        broker_config = create_broker_config()
        broker = BrokerManager(broker_config)
        
        # Register command callback
        broker.register_command_callback(on_command_received)
        
        # Register command handlers
        register_command_handlers()
        
        # Connect to broker
        if not broker.connect():
            logger.error("Failed to connect to broker")
            player.disconnect()
            return False
        
        # Start status updates if enabled
        if enable_status_updates:
            start_status_updates()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        return False


def cleanup() -> None:
    """Clean up resources."""
    global player, broker
    
    # Stop status updates
    stop_status_updates()
    
    # Disconnect from broker
    if broker:
        broker.disconnect()
    
    # Disconnect from player
    if player:
        player.disconnect()
    
    logger.info("Application stopped")


async def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()
    
    # Initialize the application
    if not initialize(config):
        logger.error("Failed to initialize application")
        return
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        cleanup()
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
        cleanup()


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
