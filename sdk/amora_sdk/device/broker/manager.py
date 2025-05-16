"""
Broker Manager for the Broker module.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union

from .client import MQTTClient
from .topics import TopicManager, TopicType
from .config import BrokerConfig, QoS
from .messages import (
    Message, StateMessage, CommandMessage, ResponseMessage,
    ConnectionMessage, parse_message
)

logger = logging.getLogger(__name__)


class BrokerManager:
    """
    Broker Manager for real-time communication using MQTT.
    
    This class provides a high-level interface for real-time communication
    between devices and client applications using MQTT. It abstracts the
    MQTT communication complexity and provides a simple pub/sub framework
    with predefined topics in the device ID namespace.
    """
    
    def __init__(self, config: BrokerConfig):
        """
        Initialize the Broker Manager.
        
        Args:
            config: Broker configuration
        """
        self.config = config
        
        # Create topic manager
        self.topic_manager = TopicManager(config.topic_prefix, config.device_id)
        
        # Create MQTT client
        self.mqtt_client = MQTTClient(
            client_id=config.client_id,
            broker_url=config.broker_url,
            port=config.port,
            options=config.connection_options
        )
        
        # Register callbacks
        self.mqtt_client.register_on_connect(self._on_connect)
        self.mqtt_client.register_on_disconnect(self._on_disconnect)
        
        # Set up last will message
        self._set_last_will()
        
        # Command handlers
        self.command_handlers: Dict[str, Callable[[CommandMessage], ResponseMessage]] = {}
        
        # Command callbacks
        self.command_callbacks: List[Callable[[CommandMessage], None]] = []
        
        # State change callbacks
        self.state_change_callbacks: List[Callable[[StateMessage], None]] = []
        
        # Connection status
        self.connected = False
    
    def _set_last_will(self) -> None:
        """Set the last will message."""
        last_will = ConnectionMessage(status="offline", timestamp=time.time())
        self.mqtt_client.set_last_will(
            topic=self.topic_manager.get_topic(TopicType.CONNECTION),
            payload=last_will.to_json(),
            qos=self.config.default_qos,
            retain=True
        )
    
    def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            True if connection was successful, False otherwise
        """
        return self.mqtt_client.connect()
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.mqtt_client.disconnect()
    
    def _on_connect(self, success: bool) -> None:
        """
        Callback for when the client connects to the broker.
        
        Args:
            success: Whether the connection was successful
        """
        if success:
            self.connected = True
            logger.info("Connected to MQTT broker")
            
            # Subscribe to command topic
            self._subscribe_to_commands()
            
            # Publish online status
            self._publish_connection_status("online")
        else:
            self.connected = False
            logger.error("Failed to connect to MQTT broker")
    
    def _on_disconnect(self) -> None:
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        logger.info("Disconnected from MQTT broker")
    
    def _subscribe_to_commands(self) -> None:
        """Subscribe to command topics."""
        for topic in self.topic_manager.get_subscription_topics():
            self.mqtt_client.subscribe(
                topic=topic,
                qos=self.config.default_qos,
                callback=self._on_command_received
            )
            logger.info(f"Subscribed to topic: {topic}")
    
    def _on_command_received(self, topic: str, payload: bytes, properties: Dict[str, Any]) -> None:
        """
        Callback for when a command is received.
        
        Args:
            topic: Topic the message was received on
            payload: Message payload
            properties: Message properties
        """
        logger.info(f"Received command on topic: {topic}")
        
        # Parse the command message
        command_msg = parse_message(payload, 'command')
        if not command_msg or not isinstance(command_msg, CommandMessage):
            logger.error(f"Invalid command message received on topic {topic}")
            return
        
        # Execute the command
        response = self._execute_command(command_msg)
        
        # Publish the response
        self.publish_response(response)
        
        # Notify command callbacks
        for callback in self.command_callbacks:
            try:
                callback(command_msg)
            except Exception as e:
                logger.error(f"Error in command callback: {e}")
    
    def _execute_command(self, command_msg: CommandMessage) -> ResponseMessage:
        """
        Execute a command.
        
        Args:
            command_msg: Command message
            
        Returns:
            Response message
        """
        command = command_msg.command
        command_id = command_msg.command_id
        
        logger.info(f"Executing command: {command} (ID: {command_id})")
        
        # Check if we have a handler for this command
        if command in self.command_handlers:
            try:
                # Call the command handler
                response = self.command_handlers[command](command_msg)
                return response
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                return ResponseMessage(
                    command_id=command_id,
                    result=False,
                    message=f"Error executing command: {str(e)}"
                )
        
        # If we get here, we don't know how to handle the command
        logger.warning(f"Command {command} not supported")
        return ResponseMessage(
            command_id=command_id,
            result=False,
            message=f"Command {command} not supported"
        )
    
    def register_command_handler(self, command: str,
                               handler: Callable[[CommandMessage], ResponseMessage]) -> None:
        """
        Register a command handler.
        
        Args:
            command: Command name
            handler: Command handler function
        """
        self.command_handlers[command] = handler
        logger.info(f"Registered handler for command: {command}")
    
    def register_command_callback(self, callback: Callable[[CommandMessage], None]) -> None:
        """
        Register a command callback.
        
        Args:
            callback: Command callback function
        """
        self.command_callbacks.append(callback)
    
    def register_state_change_callback(self, callback: Callable[[StateMessage], None]) -> None:
        """
        Register a state change callback.
        
        Args:
            callback: State change callback function
        """
        self.state_change_callbacks.append(callback)
    
    def publish_state(self, state: Union[StateMessage, Dict[str, Any]]) -> bool:
        """
        Publish a state update.
        
        Args:
            state: State message or dictionary
            
        Returns:
            True if publish was successful, False otherwise
        """
        if isinstance(state, dict):
            state = StateMessage.from_player_state(state)
        
        # Call state change callbacks
        for callback in self.state_change_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
        
        return self.mqtt_client.publish(
            topic=self.topic_manager.get_topic(TopicType.STATE),
            payload=state.to_json(),
            qos=self.config.default_qos,
            retain=True
        )
    
    def publish_response(self, response: ResponseMessage) -> bool:
        """
        Publish a command response.
        
        Args:
            response: Response message
            
        Returns:
            True if publish was successful, False otherwise
        """
        return self.mqtt_client.publish(
            topic=self.topic_manager.get_topic(TopicType.RESPONSES),
            payload=response.to_json(),
            qos=self.config.default_qos,
            retain=False
        )
    
    def _publish_connection_status(self, status: str) -> bool:
        """
        Publish connection status.
        
        Args:
            status: Connection status ("online" or "offline")
            
        Returns:
            True if publish was successful, False otherwise
        """
        connection_msg = ConnectionMessage(status=status, timestamp=time.time())
        return self.mqtt_client.publish(
            topic=self.topic_manager.get_topic(TopicType.CONNECTION),
            payload=connection_msg.to_json(),
            qos=self.config.default_qos,
            retain=True
        )
