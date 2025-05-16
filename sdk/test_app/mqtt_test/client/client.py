"""
MQTT Test Client

This module implements a CLI application that allows the user to send commands
to the player via MQTT and display real-time player status updates.
"""

import asyncio
import logging
import json
import time
import sys
import os
import signal
import argparse
from typing import Dict, Any, Optional, List
import curses
from datetime import datetime

# Add the SDK to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the SDK modules
from amora_sdk.device.broker import (
    BrokerManager, BrokerConfig, ConnectionOptions, QoS,
    Message, StateMessage, CommandMessage, ResponseMessage
)
from amora_sdk.device.broker.topics import TopicType, TopicManager

# Import the config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from config import get_mqtt_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mqtt_client.log'  # Log to file to avoid interfering with curses
)
logger = logging.getLogger(__name__)
# Set all loggers to DEBUG level
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.DEBUG)

class MQTTTestClient:
    """
    MQTT Test Client for demonstrating the Amora SDK.

    This class implements a CLI application that allows the user to send commands
    to the player via MQTT and display real-time player status updates.
    """

    def __init__(self, mqtt_config: Dict[str, Any]):
        """
        Initialize the MQTT Test Client.

        Args:
            mqtt_config: MQTT configuration
        """
        self.mqtt_config = mqtt_config

        # Create broker manager
        self.broker_manager = self._create_broker_manager()

        # Player state
        self.player_state: Optional[StateMessage] = None

        # Command responses
        self.command_responses: Dict[str, ResponseMessage] = {}

        # Running flag
        self.running = False

        # Curses screen
        self.screen = None

        # Command history
        self.command_history: List[str] = []
        self.history_index = 0

        # Current command
        self.current_command = ""
        self.cursor_position = 0

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
            client_id=self.mqtt_config.get("client_id", f"amora-client-{int(time.time())}"),
            device_id=self.mqtt_config.get("device_id", "amora-player-001"),
            topic_prefix=self.mqtt_config.get("topic_prefix", "amora/devices"),
            connection_options=connection_options,
            default_qos=QoS(self.mqtt_config.get("default_qos", 1))
        )

        # Create broker manager
        broker_manager = BrokerManager(broker_config)

        # Set up state change callback
        broker_manager.register_state_change_callback(self._on_state_change)

        # Subscribe to response topic manually since there's no register_response_callback method
        response_topic = broker_manager.topic_manager.get_topic(TopicType.RESPONSES)
        broker_manager.mqtt_client.subscribe(
            topic=response_topic,
            qos=broker_manager.config.default_qos,
            callback=self._on_message_received
        )

        return broker_manager

    def _on_state_change(self, state: StateMessage) -> None:
        """
        Handle state change.

        Args:
            state: State message
        """
        self.player_state = state
        self._update_display()

    def _on_message_received(self, topic: str, payload: bytes, properties: Dict[str, Any]) -> None:
        """
        Handle message received from MQTT broker.

        Args:
            topic: Topic the message was received on
            payload: Message payload
            properties: Message properties
        """
        try:
            # Parse the message
            message_json = json.loads(payload.decode('utf-8'))

            # Check if it's a response message
            if 'command_id' in message_json and 'result' in message_json:
                # Create a response message
                response = ResponseMessage(
                    command_id=message_json.get('command_id'),
                    result=message_json.get('result'),
                    message=message_json.get('message', ''),
                    data=message_json.get('data'),
                    timestamp=message_json.get('timestamp', time.time())
                )

                # Handle the response
                self._on_response(response)
        except Exception as e:
            logger.error(f"Error handling message on topic {topic}: {e}")

    def _on_response(self, response: ResponseMessage) -> None:
        """
        Handle command response.

        Args:
            response: Response message
        """
        self.command_responses[response.command_id] = response
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with current state and responses."""
        if not self.screen:
            return

        try:
            # Clear screen
            self.screen.clear()

            # Get screen dimensions
            height, width = self.screen.getmaxyx()

            # Display header
            self.screen.addstr(0, 0, "=== MQTT Test Client ===", curses.A_BOLD)
            self.screen.addstr(1, 0, f"Connected to: {self.mqtt_config.get('broker_url')}:{self.mqtt_config.get('port')}")
            self.screen.addstr(2, 0, f"Device ID: {self.mqtt_config.get('device_id')}")
            self.screen.addstr(3, 0, "=" * (width - 1))

            # Display player state
            if self.player_state:
                self.screen.addstr(5, 0, "Player State:", curses.A_BOLD)
                self.screen.addstr(6, 0, f"State: {self.player_state.state}")
                self.screen.addstr(7, 0, f"Volume: {self.player_state.volume}%")

                if self.player_state.current_song:
                    song = self.player_state.current_song
                    self.screen.addstr(9, 0, "Current Song:", curses.A_BOLD)
                    self.screen.addstr(10, 0, f"Title: {song.get('title', 'Unknown')}")
                    self.screen.addstr(11, 0, f"Artist: {song.get('artist', 'Unknown')}")
                    self.screen.addstr(12, 0, f"Album: {song.get('album', 'Unknown')}")

                    # Display progress bar if duration is available
                    if 'duration' in song and 'position' in song:
                        duration = song.get('duration', 0)
                        position = song.get('position', 0)

                        if duration > 0:
                            progress = int((position / duration) * (width - 20))
                            progress_bar = "[" + "=" * progress + " " * (width - 20 - progress) + "]"

                            # Format time as MM:SS
                            position_str = f"{int(position) // 60}:{int(position) % 60:02d}"
                            duration_str = f"{int(duration) // 60}:{int(duration) % 60:02d}"

                            self.screen.addstr(13, 0, f"Time: {position_str}/{duration_str}")
                            self.screen.addstr(14, 0, progress_bar)

            # Display command help
            self.screen.addstr(height - 10, 0, "Commands:", curses.A_BOLD)
            self.screen.addstr(height - 9, 0, "play - Start playback")
            self.screen.addstr(height - 8, 0, "pause - Pause playback")
            self.screen.addstr(height - 7, 0, "stop - Stop playback")
            self.screen.addstr(height - 6, 0, "next - Skip to next track")
            self.screen.addstr(height - 5, 0, "prev - Skip to previous track")
            self.screen.addstr(height - 4, 0, "vol <level> - Set volume (0-100)")
            self.screen.addstr(height - 3, 0, "quit - Exit the application")

            # Display command input
            self.screen.addstr(height - 2, 0, "=" * (width - 1))
            self.screen.addstr(height - 1, 0, "> " + self.current_command)

            # Position cursor
            self.screen.move(height - 1, 2 + self.cursor_position)

            # Refresh screen
            self.screen.refresh()
        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def _send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Send a command to the player.

        Args:
            command: Command name
            params: Command parameters
        """
        # Create command message
        command_message = CommandMessage(
            command=command,
            params=params,
            timestamp=time.time()
        )

        # Publish command
        topic = self.broker_manager.topic_manager.get_topic(TopicType.COMMANDS)
        self.broker_manager.mqtt_client.publish(
            topic=topic,
            payload=command_message.to_json(),
            qos=self.broker_manager.config.default_qos
        )

    def _process_command(self, command_line: str) -> None:
        """
        Process a command line.

        Args:
            command_line: Command line to process
        """
        # Add to command history
        if command_line:
            self.command_history.append(command_line)
            self.history_index = len(self.command_history)

        # Split command line into parts
        parts = command_line.strip().split()
        if not parts:
            return

        command = parts[0].lower()

        if command == "quit" or command == "exit":
            self.running = False
        elif command == "play":
            self._send_command("play")
        elif command == "pause":
            self._send_command("pause")
        elif command == "stop":
            self._send_command("stop")
        elif command == "next":
            self._send_command("next")
        elif command == "prev" or command == "previous":
            self._send_command("previous")
        elif command == "vol" or command == "volume":
            if len(parts) > 1:
                try:
                    volume = int(parts[1])
                    self._send_command("setVolume", {"volume": volume})
                except ValueError:
                    pass
        elif command == "status":
            self._send_command("getStatus")
        elif command == "playlists":
            self._send_command("getPlaylists")
        elif command == "playlist" and len(parts) > 1:
            self._send_command("playPlaylist", {"playlist": parts[1]})

    def _handle_key(self, key: int) -> None:
        """
        Handle a key press.

        Args:
            key: Key code
        """
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            # Process command
            self._process_command(self.current_command)
            self.current_command = ""
            self.cursor_position = 0
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Backspace
            if self.cursor_position > 0:
                self.current_command = (
                    self.current_command[:self.cursor_position - 1] +
                    self.current_command[self.cursor_position:]
                )
                self.cursor_position -= 1
        elif key == curses.KEY_DC:
            # Delete
            if self.cursor_position < len(self.current_command):
                self.current_command = (
                    self.current_command[:self.cursor_position] +
                    self.current_command[self.cursor_position + 1:]
                )
        elif key == curses.KEY_LEFT:
            # Left arrow
            if self.cursor_position > 0:
                self.cursor_position -= 1
        elif key == curses.KEY_RIGHT:
            # Right arrow
            if self.cursor_position < len(self.current_command):
                self.cursor_position += 1
        elif key == curses.KEY_UP:
            # Up arrow (command history)
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.current_command = self.command_history[self.history_index]
                self.cursor_position = len(self.current_command)
        elif key == curses.KEY_DOWN:
            # Down arrow (command history)
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.current_command = self.command_history[self.history_index]
                self.cursor_position = len(self.current_command)
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.current_command = ""
                self.cursor_position = 0
        elif key == curses.KEY_HOME:
            # Home
            self.cursor_position = 0
        elif key == curses.KEY_END:
            # End
            self.cursor_position = len(self.current_command)
        elif 32 <= key <= 126:
            # Printable character
            self.current_command = (
                self.current_command[:self.cursor_position] +
                chr(key) +
                self.current_command[self.cursor_position:]
            )
            self.cursor_position += 1

    async def _input_loop(self) -> None:
        """Handle user input."""
        while self.running:
            try:
                # Get key
                key = self.screen.getch()

                # Handle key
                if key != -1:
                    self._handle_key(key)
                    self._update_display()

                # Sleep a bit to avoid high CPU usage
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error handling input: {e}")
                await asyncio.sleep(1)

    async def start(self, screen) -> None:
        """
        Start the client.

        Args:
            screen: Curses screen
        """
        # Save screen
        self.screen = screen

        # Configure curses
        curses.curs_set(1)  # Show cursor
        curses.use_default_colors()  # Use terminal's default colors
        self.screen.nodelay(True)  # Non-blocking input
        self.screen.keypad(True)  # Enable special keys

        logger.info("Starting MQTT Test Client")

        # Connect to broker
        logger.info("Connecting to MQTT broker")
        if not self.broker_manager.connect():
            logger.error("Failed to connect to MQTT broker")
            return

        # Set running flag
        self.running = True

        # Start input loop
        input_task = asyncio.create_task(self._input_loop())

        # Initial display update
        self._update_display()

        # Wait for input loop to finish
        try:
            await input_task
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the client."""
        logger.info("Stopping MQTT Test Client")

        # Set running flag
        self.running = False

        # Disconnect from broker
        self.broker_manager.disconnect()

        logger.info("MQTT Test Client stopped")

async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MQTT Test Client")
    parser.add_argument("--config", help="Path to credentials file", default="credentials_configs.txt")
    args = parser.parse_args()

    # Load configuration
    mqtt_config = get_mqtt_config(args.config)

    # Check if MQTT configuration is valid
    if not mqtt_config.get("broker_url"):
        print("Error: MQTT broker URL not specified")
        print("Please create a credentials_configs.txt file with MQTT configuration")
        print("or set the MQTT_BROKER_URL environment variable")
        return

    # Create client
    client = MQTTTestClient(mqtt_config)

    # Start client with curses
    await curses.wrapper(client.start)

    # Stop client
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
