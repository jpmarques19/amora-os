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

# Configure logging with explicit console handler to ensure terminal output
# Remove all existing handlers to avoid duplicate messages
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the root logger
logging.root.setLevel(logging.DEBUG)
logging.root.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

# Create a custom formatter for MQTT messages
mqtt_formatter = logging.Formatter('%(asctime)s - MQTT - %(levelname)s - %(message)s')

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

        # Add custom message handler to log all MQTT messages
        def custom_message_handler(topic, payload, properties):
            try:
                if isinstance(payload, bytes):
                    payload_str = payload.decode('utf-8')
                else:
                    payload_str = str(payload)

                # Try to parse as JSON for better formatting
                try:
                    payload_json = json.loads(payload_str)
                    payload_formatted = json.dumps(payload_json, indent=2)
                except:
                    payload_formatted = payload_str

                # Use print to ensure it shows in the terminal
                print(f"\n===== MQTT MESSAGE RECEIVED =====", flush=True)
                print(f"Topic: {topic}", flush=True)
                print(f"Payload: {payload_formatted}", flush=True)
                print(f"Properties: {properties}", flush=True)
                print(f"=================================\n", flush=True)

                # Also log it
                logger.info(f"MQTT Message Received: Topic: {topic}")
            except Exception as e:
                print(f"\n===== ERROR IN MQTT MESSAGE HANDLER =====", flush=True)
                print(f"Error: {e}", flush=True)
                print(f"==========================================\n", flush=True)
                logger.error(f"Error in custom message handler: {e}")

        # Add the custom handler to the MQTT client by subscribing to all topics
        # We'll use a wildcard subscription to catch all messages
        broker_manager.mqtt_client.subscribe(
            topic="#",  # Wildcard for all topics
            qos=QoS.AT_LEAST_ONCE,
            callback=custom_message_handler
        )

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

    def _handle_play(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle play command.

        Args:
            command: Command message

        Returns:
            Response message
        """
        print(f"\n===== HANDLING PLAY COMMAND =====", flush=True)
        print(f"Command ID: {command.command_id}", flush=True)
        print(f"Command details: {json.dumps(command.to_dict(), indent=2)}", flush=True)

        # Execute the command
        try:
            result = self.player.play()
            print(f"Play command result: {result}", flush=True)

            # Get current status after command execution
            status = self.player.get_status()
            print(f"Player status after play command: {json.dumps(status, indent=2)}", flush=True)

            # Create response
            response = ResponseMessage(
                command_id=command.command_id,
                result=result,
                message="Play command executed",
                timestamp=time.time()
            )
            print(f"Response: {json.dumps(response.to_dict(), indent=2)}", flush=True)
            print(f"=================================\n", flush=True)

            # Also log it
            logger.info(f"Play command executed (ID: {command.command_id}), result: {result}")
            return response
        except Exception as e:
            print(f"\n===== ERROR EXECUTING PLAY COMMAND =====", flush=True)
            print(f"Error: {e}", flush=True)
            print(f"==========================================\n", flush=True)

            logger.error(f"Error executing play command: {e}")
            response = ResponseMessage(
                command_id=command.command_id,
                result=False,
                message=f"Error executing play command: {str(e)}",
                timestamp=time.time()
            )
            return response

    def _handle_pause(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle pause command.

        Args:
            command: Command message

        Returns:
            Response message
        """
        print(f"\n===== HANDLING PAUSE COMMAND =====")
        print(f"Command ID: {command.command_id}")
        print(f"Command details: {json.dumps(command.to_dict(), indent=2)}")

        # Execute the command
        try:
            result = self.player.pause()
            print(f"Pause command result: {result}")

            # Get current status after command execution
            status = self.player.get_status()
            print(f"Player status after pause command: {json.dumps(status, indent=2)}")

            # Create response
            response = ResponseMessage(
                command_id=command.command_id,
                result=result,
                message="Pause command executed",
                timestamp=time.time()
            )
            print(f"Response: {json.dumps(response.to_dict(), indent=2)}")
            print(f"=================================\n")

            # Also log it
            logger.info(f"Pause command executed (ID: {command.command_id}), result: {result}")
            return response
        except Exception as e:
            print(f"\n===== ERROR EXECUTING PAUSE COMMAND =====")
            print(f"Error: {e}")
            print(f"==========================================\n")

            logger.error(f"Error executing pause command: {e}")
            response = ResponseMessage(
                command_id=command.command_id,
                result=False,
                message=f"Error executing pause command: {str(e)}",
                timestamp=time.time()
            )
            return response

    def _handle_stop(self, command: CommandMessage) -> ResponseMessage:
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

    def _handle_next(self, command: CommandMessage) -> ResponseMessage:
        """
        Handle next command.

        Args:
            command: Command message

        Returns:
            Response message
        """
        print(f"\n===== HANDLING NEXT COMMAND =====")
        print(f"Command ID: {command.command_id}")
        print(f"Command details: {json.dumps(command.to_dict(), indent=2)}")

        # Execute the command
        try:
            result = self.player.next()
            print(f"Next command result: {result}")

            # Get current status after command execution
            status = self.player.get_status()
            print(f"Player status after next command: {json.dumps(status, indent=2)}")

            # Create response
            response = ResponseMessage(
                command_id=command.command_id,
                result=result,
                message="Next command executed",
                timestamp=time.time()
            )
            print(f"Response: {json.dumps(response.to_dict(), indent=2)}")
            print(f"=================================\n")

            # Also log it
            logger.info(f"Next command executed (ID: {command.command_id}), result: {result}")
            return response
        except Exception as e:
            print(f"\n===== ERROR EXECUTING NEXT COMMAND =====")
            print(f"Error: {e}")
            print(f"==========================================\n")

            logger.error(f"Error executing next command: {e}")
            response = ResponseMessage(
                command_id=command.command_id,
                result=False,
                message=f"Error executing next command: {str(e)}",
                timestamp=time.time()
            )
            return response

    def _handle_previous(self, command: CommandMessage) -> ResponseMessage:
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

    def _handle_set_volume(self, command: CommandMessage) -> ResponseMessage:
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

    def _handle_get_status(self, command: CommandMessage) -> ResponseMessage:
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

    def _handle_get_playlists(self, command: CommandMessage) -> ResponseMessage:
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

    def _handle_play_playlist(self, command: CommandMessage) -> ResponseMessage:
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
        last_state = None
        last_song_title = None
        while self.running:
            try:
                # Get player status
                status = self.player.get_status()

                # Check if state has changed
                current_state = status.get('state', '')
                current_song = status.get('current_song', {})
                current_song_title = current_song.get('title', '') if current_song else ''

                # Log state changes or song changes
                if (last_state is None or last_state != current_state or
                    last_song_title is None or last_song_title != current_song_title):
                    print(f"\n===== PLAYER STATE UPDATE =====", flush=True)
                    print(f"State: {current_state}", flush=True)
                    if current_song:
                        print(f"Current song: {current_song_title}", flush=True)
                        print(f"Artist: {current_song.get('artist', 'Unknown')}", flush=True)
                        print(f"Album: {current_song.get('album', 'Unknown')}", flush=True)
                    print(f"===============================\n", flush=True)

                    last_state = current_state
                    last_song_title = current_song_title

                # Create state message
                state_message = StateMessage.from_player_state(status)

                # Publish state
                publish_result = self.broker_manager.publish_state(state_message)
                if not publish_result:
                    print(f"\n===== ERROR PUBLISHING STATE =====", flush=True)
                    print(f"Failed to publish state message", flush=True)
                    print(f"==================================\n", flush=True)
                    logger.warning("Failed to publish state message")

                # Wait for next update
                await asyncio.sleep(self.status_update_interval)
            except Exception as e:
                print(f"\n===== ERROR UPDATING STATUS =====", flush=True)
                print(f"Error: {e}", flush=True)
                print(f"=================================\n", flush=True)
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
