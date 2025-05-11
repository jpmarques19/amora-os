"""
Device twin module for AmoraSDK Device.

This module handles device twin synchronization with Azure IoT Hub.
"""

import logging
import time
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

class TwinManager:
    """Manages device twin for the IoT device client."""
    
    def __init__(self, client, player_interface):
        """
        Initialize the twin manager.
        
        Args:
            client: IoT Hub device client
            player_interface: Player interface
        """
        self.client = client
        self.player = player_interface
        self.desired_property_handlers = {}
        
        # Register default handlers
        self.register_desired_property_handler("volume", self._handle_volume)
        self.register_desired_property_handler("telemetry_interval", self._handle_telemetry_interval)
        self.register_desired_property_handler("repeat", self._handle_repeat)
        self.register_desired_property_handler("random", self._handle_random)
        
    def register_desired_property_handler(self, property_name: str, handler: Callable[[Any], None]):
        """
        Register a handler for a desired property.
        
        Args:
            property_name (str): Name of the property
            handler (Callable[[Any], None]): Handler function
        """
        self.desired_property_handlers[property_name] = handler
        
    async def handle_desired_properties(self, patch: Dict[str, Any]):
        """
        Handle desired property changes.
        
        Args:
            patch (Dict[str, Any]): Desired property patch
        """
        logger.info(f"Desired property patch received: {patch}")
        
        # Process desired properties
        for property_name, value in patch.items():
            if property_name in self.desired_property_handlers:
                try:
                    await self.desired_property_handlers[property_name](value)
                except Exception as e:
                    logger.error(f"Error handling desired property {property_name}: {e}")
        
        # Update reported properties
        await self.update_reported_properties()
        
    async def update_reported_properties(self):
        """Update reported properties in device twin."""
        try:
            if not self.client.connected:
                logger.debug("Skipping reported properties update - not connected to IoT Hub")
                return
            
            # Get player status
            status = self.player.get_status()
            
            # Create reported properties
            reported_properties = {
                "status": status,
                "telemetry_interval": self.client.telemetry_interval,
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            # Update reported properties
            await self.client.patch_twin_reported_properties(reported_properties)
            logger.debug(f"Reported properties updated: {reported_properties}")
            
        except Exception as e:
            logger.error(f"Error updating reported properties: {e}")
    
    async def _handle_volume(self, volume: int):
        """
        Handle volume desired property.
        
        Args:
            volume (int): Volume level
        """
        logger.info(f"Setting volume to {volume}")
        result = self.player.set_volume(volume)
        logger.info(f"Volume set to {volume}: {result}")
        
    async def _handle_telemetry_interval(self, interval: int):
        """
        Handle telemetry interval desired property.
        
        Args:
            interval (int): Telemetry interval in seconds
        """
        logger.info(f"Setting telemetry interval to {interval} seconds")
        self.client.telemetry_interval = interval
        
    async def _handle_repeat(self, repeat: bool):
        """
        Handle repeat desired property.
        
        Args:
            repeat (bool): Repeat mode
        """
        logger.info(f"Setting repeat mode to {repeat}")
        result = self.player.set_repeat(repeat)
        logger.info(f"Repeat mode set to {repeat}: {result}")
        
    async def _handle_random(self, random: bool):
        """
        Handle random desired property.
        
        Args:
            random (bool): Random mode
        """
        logger.info(f"Setting random mode to {random}")
        result = self.player.set_random(random)
        logger.info(f"Random mode set to {random}: {result}")
