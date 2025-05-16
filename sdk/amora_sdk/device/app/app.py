"""
Application implementation for AmoraSDK Device.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List, Union

from ..broker.manager import BrokerManager
from ..broker.config import BrokerConfig
from ..broker.messages import CommandMessage, StateMessage, ResponseMessage

logger = logging.getLogger(__name__)


class AmoraApp:
    """
    Amora Application class that integrates the player and broker modules.
    
    This class handles the communication between the player and broker modules,
    ensuring they remain decoupled from each other.
    """
    
    def __init__(self, player_interface, broker_config: BrokerConfig, config: Dict[str, Any] = None):
        """
        Initialize the Amora Application.
        
        Args:
            player_interface: Player interface instance
            broker_config: Broker configuration
            config: Application configuration
        """
        self.player = player_interface
        self.config = config or {}
        
        # Create broker manager
        self.broker = BrokerManager(broker_config)
        
        # Register command callback
        self.broker.register_command_callback(self._on_command_received)
        
        # Status update configuration
        self.update_interval = self.config.get("status_updater", {}).get("update_interval", 1.0)  # seconds
        self.position_update_interval = self.config.get("status_updater", {}).get("position_update_interval", 1.0)  # seconds
        self.full_update_interval = self.config.get("status_updater", {}).get("full_update_interval", 5.0)  # seconds
        self.enable_status_updates = self.config.get("status_updater", {}).get("enabled", True)
        
        # Status update state
        self.running = False
        self.update_thread = None
        self.last_status: Optional[Dict[str, Any]] = None
        self.last_full_update_time = 0
        self.last_position_update_time = 0
        
        # Command handlers
        self._register_command_handlers()
    
    def _register_command_handlers(self) -> None:
        """Register command handlers for standard player commands."""
        # Register handlers for standard player commands
        standard_commands = [
            "play", "pause", "stop", "next", "previous", 
            "set_volume", "get_volume", "get_status", "get_playlists",
            "play_playlist", "set_repeat", "set_random", 
            "create_playlist", "delete_playlist", "get_playlist_songs",
            "update_database"
        ]
        
        for command in standard_commands:
            self.broker.register_command_handler(command, self._create_command_handler(command))
    
    def _create_command_handler(self, command: str) -> Callable[[CommandMessage], ResponseMessage]:
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
                method = getattr(self.player, command, None)
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
                    self._update_player_state()
                    
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
    
    def _on_command_received(self, command_msg: CommandMessage) -> None:
        """
        Handle received command.
        
        Args:
            command_msg: Command message
        """
        logger.debug(f"Command received: {command_msg.command}")
        # The actual command execution is handled by the registered command handlers
    
    def connect(self) -> bool:
        """
        Connect to services.
        
        Returns:
            True if connection was successful, False otherwise
        """
        # Connect to broker
        broker_connected = self.broker.connect()
        
        # Start status updates if enabled
        if broker_connected and self.enable_status_updates:
            self.start_status_updates()
        
        return broker_connected
    
    def disconnect(self) -> None:
        """Disconnect from services."""
        # Stop status updates
        self.stop_status_updates()
        
        # Disconnect from broker
        self.broker.disconnect()
    
    def start_status_updates(self) -> bool:
        """
        Start status updates.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Status updates already running")
            return True
        
        if not self.enable_status_updates:
            logger.info("Status updates are disabled in configuration")
            return False
        
        self.running = True
        self.update_thread = threading.Thread(target=self._status_update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Player status updates started")
        return True
    
    def stop_status_updates(self) -> None:
        """Stop status updates."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        logger.info("Player status updates stopped")
    
    def _status_update_loop(self) -> None:
        """Main status update loop."""
        while self.running:
            try:
                self._check_and_update_status()
            except Exception as e:
                logger.error(f"Error in status update loop: {e}")
            
            # Sleep for the update interval
            time.sleep(self.update_interval)
    
    def _check_and_update_status(self) -> None:
        """Check player status and publish updates if needed."""
        current_time = time.time()
        
        # Get current status
        current_status = self.player.get_status()
        
        # Determine if we need to send an update
        send_update = False
        send_full_update = False
        
        # Always send a full update periodically
        if current_time - self.last_full_update_time >= self.full_update_interval:
            send_update = True
            send_full_update = True
            self.last_full_update_time = current_time
        
        # Send position updates more frequently when playing
        elif (current_status.get("state") == "play" and 
              current_time - self.last_position_update_time >= self.position_update_interval):
            send_update = True
            self.last_position_update_time = current_time
        
        # Check for state changes
        elif self.last_status is not None:
            # Check if playback state changed
            if current_status.get("state") != self.last_status.get("state"):
                send_update = True
                send_full_update = True
            
            # Check if current song changed
            elif (current_status.get("current_song") is not None and 
                  self.last_status.get("current_song") is not None and
                  current_status.get("current_song").get("file") != 
                  self.last_status.get("current_song").get("file")):
                send_update = True
                send_full_update = True
            
            # Check if volume changed
            elif current_status.get("volume") != self.last_status.get("volume"):
                send_update = True
            
            # Check if repeat or random changed
            elif (current_status.get("repeat") != self.last_status.get("repeat") or
                  current_status.get("random") != self.last_status.get("random")):
                send_update = True
        else:
            # First update
            send_update = True
            send_full_update = True
        
        # Send the update if needed
        if send_update:
            if send_full_update:
                # Send full status update
                self._update_player_state()
            else:
                # For position updates, we can optimize by only sending the position
                if current_status.get("state") == "play" and current_status.get("current_song"):
                    position_update = {
                        "state": current_status.get("state"),
                        "current_song": {
                            "position": current_status.get("current_song", {}).get("position", 0)
                        }
                    }
                    self.broker.publish_state(position_update)
                else:
                    # For other changes, send the full update
                    self._update_player_state()
        
        # Update last status
        self.last_status = current_status
    
    def _update_player_state(self) -> bool:
        """
        Update the player state.
        
        This method gets the current state from the player interface and
        publishes it to the broker.
        
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get the current state from the player interface
            state = self.player.get_status()
            
            # Publish the state
            return self.broker.publish_state(state)
        except Exception as e:
            logger.error(f"Error updating player state: {e}")
            return False
