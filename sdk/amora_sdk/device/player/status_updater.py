"""
Player Status Updater module for AmoraSDK Device.

Handles automatic updates of player status via MQTT.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class PlayerStatusUpdater:
    """
    Player Status Updater class for sending real-time player status updates.
    
    This class periodically checks the player status and publishes updates
    when changes are detected or at regular intervals.
    """
    
    def __init__(self, player_interface, broker_manager, config: Dict[str, Any]):
        """
        Initialize the Player Status Updater.
        
        Args:
            player_interface: Player interface instance
            broker_manager: Broker manager instance
            config (Dict[str, Any]): Configuration dictionary
        """
        self.player = player_interface
        self.broker = broker_manager
        self.config = config
        
        # Configuration options
        self.update_interval = config.get("status_updater", {}).get("update_interval", 1.0)  # seconds
        self.position_update_interval = config.get("status_updater", {}).get("position_update_interval", 1.0)  # seconds
        self.full_update_interval = config.get("status_updater", {}).get("full_update_interval", 5.0)  # seconds
        self.enabled = config.get("status_updater", {}).get("enabled", True)
        
        # State tracking
        self.running = False
        self.update_thread = None
        self.last_status: Optional[Dict[str, Any]] = None
        self.last_full_update_time = 0
        self.last_position_update_time = 0
    
    def start(self) -> bool:
        """
        Start the status updater.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Status updater is already running")
            return True
        
        if not self.enabled:
            logger.info("Status updater is disabled in configuration")
            return False
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Player status updater started")
        return True
    
    def stop(self) -> None:
        """Stop the status updater."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        logger.info("Player status updater stopped")
    
    def _update_loop(self) -> None:
        """Main update loop."""
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
                self.broker.update_player_state()
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
                    self.broker.update_player_state()
        
        # Update last status
        self.last_status = current_status
