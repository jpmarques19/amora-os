"""
MQTT Test Server

This module implements a server that uses the Amora SDK to set up the player,
configure MQTT broker communication, handle incoming commands from the client,
and broadcast player status updates via MQTT.
"""

import asyncio
import logging
import json
import time
import sys
import os
import signal
from typing import Dict, Any, Optional

# Add the SDK to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the SDK modules
from amora_sdk.device.broker import (
    BrokerManager, BrokerConfig, ConnectionOptions, QoS,
    Message, StateMessage, CommandMessage, ResponseMessage
)
from amora_sdk.device.broker.topics import TopicType
from amora_sdk.device.player.music_player import MusicPlayer

# Import the config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from config import get_mqtt_config, get_player_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTTestServer:
    """
    MQTT Test Server for demonstrating the Amora SDK.
    
    This class sets up a server that uses the Amora SDK to control the music player
    via MQTT commands and broadcast player status updates.
    """
    
    def __init__(self, mqtt_config: Dict[str, Any], player_config: Dict[str, Any]):
        """
        Initialize the MQTT Test Server.
        
        Args:
            mqtt_config: MQTT configuration
            player_config: Player configuration
        """
        self.mqtt_config = mqtt_config
        self.player_config = player_config
        
        # Create player interface
        self.player = self._create_player()
        
        # Create broker manager
        self.broker_manager = self._create_broker_manager()
        
        # Set up command handlers
        self._setup_command_handlers()
        
        # Status update interval in seconds
        self.status_update_interval = 1.0
        
        # Running flag
        self.running = False
        
        # Status update task
        self.status_update_task = None
    
    def _create_player(self) -> MusicPlayer:
        """
        Create the player interface.
        
        Returns:
            MusicPlayer instance
        """
        mpd_config = {
            "mpd": {
                "host": self.player_config.get("mpd_host", "localhost"),
                "port": self.player_config.get("mpd_port", 6600)
            },
            "content": {
                "storage_path": self.player_config.get("storage_path", "/home/user/music"),
                "playlists_path": self.player_config.get("playlists_path", "/home/user/music/playlists")
            },
            "audio": {
                "backend": self.player_config.get("audio_backend", "pipewire"),
                "device": self.player_config.get("audio_device", "default"),
                "volume": self.player_config.get("audio_volume", 80)
            },
            "dev_mode": self.player_config.get("dev_mode", True)
        }
        
        player = MusicPlayer(mpd_config)
        return player
    
    def _create_broker_manager(self) -> BrokerManager:
        """
        Create the broker manager.
        
        Returns:
            BrokerManager instance
        """
        # Create connection options
        connection_options = ConnectionOptions(
            use_tls=self.mqtt_config.get("use_tls", False),
            username=self.mqtt_config.get("username"),
            password=self.mqtt_config.get("password"),
            keep_alive=self.mqtt_config.get("keep_alive", 60),
            clean_session=self.mqtt_config.get("clean_session", True),
            reconnect_on_failure=self.mqtt_config.get("reconnect_on_failure", True),
            max_reconnect_delay=self.mqtt_config.get("max_reconnect_delay", 300)
        )
        
        # Create broker config
        broker_config = BrokerConfig(
            broker_url=self.mqtt_config.get("broker_url", "localhost"),
            port=self.mqtt_config.get("port", 1883),
            client_id=self.mqtt_config.get("client_id", f"amora-server-{int(time.time())}"),
            device_id=self.mqtt_config.get("device_id", "amora-player-001"),
            topic_prefix=self.mqtt_config.get("topic_prefix", "amora/devices"),
            connection_options=connection_options,
            default_qos=QoS(self.mqtt_config.get("default_qos", 1))
        )
        
        # Create broker manager
        broker_manager = BrokerManager(broker_config, self.player)
        return broker_manager
    
    def _setup_command_handlers(self) -> None:
        """Set up command handlers for the broker manager."""
        # Register command handlers
        self.broker_manager.register_command_handler("play", self._handle_play)
        self.broker_manager.register_command_handler("pause", self._handle_pause)
        self.broker_manager.register_command_handler("stop", self._handle_stop)
        self.broker_manager.register_command_handler("next", self._handle_next)
        self.broker_manager.register_command_handler("previous", self._handle_previous)
        self.broker_manager.register_command_handler("setVolume", self._handle_set_volume)
        self.broker_manager.register_command_handler("getStatus", self._handle_get_status)
        self.broker_manager.register_command_handler("getPlaylists", self._handle_get_playlists)
        self.broker_manager.register_command_handler("playPlaylist", self._handle_play_playlist)
    
    async def _handle_play(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle play command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling play command")
        result = self.player.play()
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message="Play command executed",
            timestamp=time.time()
        )
    
    async def _handle_pause(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle pause command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling pause command")
        result = self.player.pause()
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message="Pause command executed",
            timestamp=time.time()
        )
    
    async def _handle_stop(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle stop command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling stop command")
        result = self.player.stop()
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message="Stop command executed",
            timestamp=time.time()
        )
    
    async def _handle_next(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle next command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling next command")
        result = self.player.next()
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message="Next command executed",
            timestamp=time.time()
        )
    
    async def _handle_previous(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle previous command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling previous command")
        result = self.player.previous()
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message="Previous command executed",
            timestamp=time.time()
        )
    
    async def _handle_set_volume(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle setVolume command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling setVolume command")
        params = command.params or {}
        volume = params.get("volume", 50)
        
        result = self.player.set_volume(volume)
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message=f"Volume set to {volume}",
            timestamp=time.time()
        )
    
    async def _handle_get_status(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle getStatus command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling getStatus command")
        status = self.player.get_status()
        return ResponseMessage(
            command_id=command.command_id,
            result=True,
            message="Status retrieved",
            data={"status": status},
            timestamp=time.time()
        )
    
    async def _handle_get_playlists(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle getPlaylists command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling getPlaylists command")
        playlists = self.player.get_playlists()
        return ResponseMessage(
            command_id=command.command_id,
            result=True,
            message="Playlists retrieved",
            data={"playlists": playlists},
            timestamp=time.time()
        )
    
    async def _handle_play_playlist(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle playPlaylist command.
        
        Args:
            command: Command message
            
        Returns:
            Response message
        """
        logger.info("Handling playPlaylist command")
        params = command.params or {}
        playlist = params.get("playlist")
        
        if not playlist:
            return ResponseMessage(
                command_id=command.command_id,
                result=False,
                message="No playlist specified",
                timestamp=time.time()
            )
        
        result = self.player.play_playlist(playlist)
        return ResponseMessage(
            command_id=command.command_id,
            result=result,
            message=f"Playing playlist {playlist}",
            timestamp=time.time()
        )
    
    async def _update_status(self) -> None:
        """Periodically update and publish player status."""
        while self.running:
            try:
                # Get player status
                status = self.player.get_status()
                
                # Create state message
                state_message = StateMessage.from_player_state(status)
                
                # Publish state
                self.broker_manager.publish_state(state_message)
                
                # Wait for next update
                await asyncio.sleep(self.status_update_interval)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                await asyncio.sleep(1)  # Wait a bit before retrying
    
    async def start(self) -> None:
        """Start the server."""
        logger.info("Starting MQTT Test Server")
        
        # Connect to player
        if not self.player.connected:
            logger.info("Connecting to player")
            if not self.player.connect():
                logger.error("Failed to connect to player")
                return
        
        # Connect to broker
        logger.info("Connecting to MQTT broker")
        if not self.broker_manager.connect():
            logger.error("Failed to connect to MQTT broker")
            return
        
        # Set running flag
        self.running = True
        
        # Start status update task
        self.status_update_task = asyncio.create_task(self._update_status())
        
        logger.info("MQTT Test Server started")
    
    async def stop(self) -> None:
        """Stop the server."""
        logger.info("Stopping MQTT Test Server")
        
        # Set running flag
        self.running = False
        
        # Cancel status update task
        if self.status_update_task:
            self.status_update_task.cancel()
            try:
                await self.status_update_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect from broker
        self.broker_manager.disconnect()
        
        # Disconnect from player
        self.player.disconnect()
        
        logger.info("MQTT Test Server stopped")

async def main():
    """Main function."""
    # Load configuration
    mqtt_config = get_mqtt_config()
    player_config = get_player_config()
    
    # Check if MQTT configuration is valid
    if not mqtt_config.get("broker_url"):
        logger.error("MQTT broker URL not specified")
        return
    
    # Create server
    server = MQTTTestServer(mqtt_config, player_config)
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(server)))
    
    # Start server
    await server.start()
    
    # Keep running until stopped
    try:
        while server.running:
            await asyncio.sleep(1)
    finally:
        await server.stop()

async def shutdown(server: MQTTTestServer):
    """Shutdown the server."""
    logger.info("Shutting down...")
    await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
