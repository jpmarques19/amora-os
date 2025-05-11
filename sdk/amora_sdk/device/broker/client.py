"""
MQTT client wrapper for the Broker module.
"""

import json
import logging
import time
import ssl
import threading
from typing import Dict, Any, Optional, Callable, List, Union

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("Paho MQTT client not available. MQTT functionality will be disabled.")
    MQTT_AVAILABLE = False
    # Define a dummy class for type hints
    class mqtt:
        """Dummy MQTT class for type hints."""
        class Client:
            """Dummy Client class for type hints."""
            pass

from .config import ConnectionOptions, QoS

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    MQTT client wrapper for the Broker module.
    
    This class provides a wrapper around the Paho MQTT client with additional
    functionality for connection management, reconnection, and error handling.
    """
    
    def __init__(self, client_id: str, broker_url: str, port: int, options: ConnectionOptions):
        """
        Initialize the MQTT client.
        
        Args:
            client_id: Client ID
            broker_url: MQTT broker URL
            port: MQTT broker port
            options: Connection options
        """
        if not MQTT_AVAILABLE:
            raise ImportError("Paho MQTT client not available. Cannot create MQTT client.")
        
        self.client_id = client_id
        self.broker_url = broker_url
        self.port = port
        self.options = options
        
        self.client = mqtt.Client(client_id=client_id, clean_session=options.clean_session)
        self.connected = False
        self.reconnect_timer = None
        self.reconnect_delay = 1  # Initial reconnect delay in seconds
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        
        # User callbacks
        self.on_connect_callbacks: List[Callable[[bool], None]] = []
        self.on_disconnect_callbacks: List[Callable[[], None]] = []
        self.on_message_callbacks: Dict[str, List[Callable[[str, bytes, Dict[str, Any]], None]]] = {}
        
        # Configure TLS if needed
        if options.use_tls:
            self._configure_tls()
        
        # Configure authentication if needed
        if options.username and options.password:
            self.client.username_pw_set(options.username, options.password)
    
    def _configure_tls(self) -> None:
        """Configure TLS for the MQTT client."""
        if self.options.cert_file and self.options.key_file:
            # Client certificate authentication
            self.client.tls_set(
                ca_certs=self.options.ca_file,
                certfile=self.options.cert_file,
                keyfile=self.options.key_file,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
        elif self.options.ca_file:
            # Server certificate verification only
            self.client.tls_set(
                ca_certs=self.options.ca_file,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
        else:
            # Default TLS configuration
            self.client.tls_set(
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
    
    def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker_url}:{self.port}")
            self.client.connect(
                self.broker_url,
                self.port,
                keepalive=self.options.keep_alive
            )
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            if self.options.reconnect_on_failure:
                self._schedule_reconnect()
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
        
        try:
            self.client.disconnect()
            self.client.loop_stop()
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def publish(self, topic: str, payload: Union[str, Dict[str, Any], bytes],
                qos: QoS = QoS.AT_LEAST_ONCE, retain: bool = False) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            qos: Quality of Service level
            retain: Whether to retain the message
            
        Returns:
            True if publish was successful, False otherwise
        """
        if not self.connected:
            logger.warning("Cannot publish: not connected to MQTT broker")
            return False
        
        try:
            # Convert payload to JSON string if it's a dictionary
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            # Convert payload to bytes if it's a string
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            result = self.client.publish(topic, payload, qos.value, retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Error publishing to topic {topic}: {e}")
            return False
    
    def subscribe(self, topic: str, qos: QoS = QoS.AT_LEAST_ONCE,
                  callback: Optional[Callable[[str, bytes, Dict[str, Any]], None]] = None) -> bool:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            qos: Quality of Service level
            callback: Callback function for messages on this topic
            
        Returns:
            True if subscription was successful, False otherwise
        """
        if not self.connected:
            logger.warning("Cannot subscribe: not connected to MQTT broker")
            return False
        
        try:
            if callback:
                if topic not in self.on_message_callbacks:
                    self.on_message_callbacks[topic] = []
                self.on_message_callbacks[topic].append(callback)
            
            result = self.client.subscribe(topic, qos.value)
            return result[0] == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        if not self.connected:
            logger.warning("Cannot unsubscribe: not connected to MQTT broker")
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            if topic in self.on_message_callbacks:
                del self.on_message_callbacks[topic]
            return result[0] == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
            return False
    
    def set_last_will(self, topic: str, payload: Union[str, Dict[str, Any], bytes],
                      qos: QoS = QoS.AT_LEAST_ONCE, retain: bool = True) -> None:
        """
        Set the last will message.
        
        Args:
            topic: Topic for the last will message
            payload: Last will message payload
            qos: Quality of Service level
            retain: Whether to retain the message
        """
        try:
            # Convert payload to JSON string if it's a dictionary
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            # Convert payload to bytes if it's a string
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            self.client.will_set(topic, payload, qos.value, retain)
            logger.info(f"Last will message set for topic {topic}")
        except Exception as e:
            logger.error(f"Error setting last will message: {e}")
    
    def register_on_connect(self, callback: Callable[[bool], None]) -> None:
        """
        Register a callback for connection events.
        
        Args:
            callback: Callback function
        """
        self.on_connect_callbacks.append(callback)
    
    def register_on_disconnect(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for disconnection events.
        
        Args:
            callback: Callback function
        """
        self.on_disconnect_callbacks.append(callback)
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """
        Callback for when the client connects to the broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Result code
        """
        if rc == 0:
            self.connected = True
            self.reconnect_delay = 1  # Reset reconnect delay
            logger.info("Connected to MQTT broker")
            
            # Call user callbacks
            for callback in self.on_connect_callbacks:
                try:
                    callback(True)
                except Exception as e:
                    logger.error(f"Error in on_connect callback: {e}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")
            
            # Call user callbacks
            for callback in self.on_connect_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    logger.error(f"Error in on_connect callback: {e}")
            
            # Schedule reconnect if enabled
            if self.options.reconnect_on_failure:
                self._schedule_reconnect()
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """
        Callback for when the client disconnects from the broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            rc: Result code
        """
        self.connected = False
        
        if rc == 0:
            logger.info("Disconnected from MQTT broker")
        else:
            logger.warning(f"Unexpected disconnection from MQTT broker with result code {rc}")
            
            # Schedule reconnect if enabled
            if self.options.reconnect_on_failure:
                self._schedule_reconnect()
        
        # Call user callbacks
        for callback in self.on_disconnect_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in on_disconnect callback: {e}")
    
    def _on_message(self, client, userdata, msg) -> None:
        """
        Callback for when a message is received from the broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: Message
        """
        logger.debug(f"Received message on topic {msg.topic}")
        
        # Call topic-specific callbacks
        if msg.topic in self.on_message_callbacks:
            for callback in self.on_message_callbacks[msg.topic]:
                try:
                    callback(msg.topic, msg.payload, {"qos": msg.qos, "retain": msg.retain})
                except Exception as e:
                    logger.error(f"Error in on_message callback for topic {msg.topic}: {e}")
        
        # Call wildcard callbacks
        for topic, callbacks in self.on_message_callbacks.items():
            if '+' in topic or '#' in topic:
                if self._topic_matches_subscription(topic, msg.topic):
                    for callback in callbacks:
                        try:
                            callback(msg.topic, msg.payload, {"qos": msg.qos, "retain": msg.retain})
                        except Exception as e:
                            logger.error(f"Error in on_message callback for wildcard topic {topic}: {e}")
    
    def _on_publish(self, client, userdata, mid) -> None:
        """
        Callback for when a message is published.
        
        Args:
            client: MQTT client instance
            userdata: User data
            mid: Message ID
        """
        logger.debug(f"Message {mid} published")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos) -> None:
        """
        Callback for when a subscription is made.
        
        Args:
            client: MQTT client instance
            userdata: User data
            mid: Message ID
            granted_qos: Granted QoS levels
        """
        logger.debug(f"Subscription {mid} made with QoS {granted_qos}")
    
    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
        
        logger.info(f"Scheduling reconnect in {self.reconnect_delay} seconds")
        self.reconnect_timer = threading.Timer(self.reconnect_delay, self._reconnect)
        self.reconnect_timer.daemon = True
        self.reconnect_timer.start()
        
        # Exponential backoff with max delay
        self.reconnect_delay = min(self.reconnect_delay * 2, self.options.max_reconnect_delay)
    
    def _reconnect(self) -> None:
        """Attempt to reconnect to the MQTT broker."""
        if not self.connected:
            try:
                logger.info(f"Attempting to reconnect to MQTT broker at {self.broker_url}:{self.port}")
                self.client.reconnect()
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT broker: {e}")
                self._schedule_reconnect()
    
    def _topic_matches_subscription(self, subscription: str, topic: str) -> bool:
        """
        Check if a topic matches a subscription pattern.
        
        Args:
            subscription: Subscription pattern
            topic: Topic to check
            
        Returns:
            True if the topic matches the subscription, False otherwise
        """
        # Split the subscription and topic into parts
        subscription_parts = subscription.split('/')
        topic_parts = topic.split('/')
        
        # If the subscription has more parts than the topic, it can't match
        if len(subscription_parts) > len(topic_parts) and '#' not in subscription_parts:
            return False
        
        # Check each part
        for i, sub_part in enumerate(subscription_parts):
            # If we've reached the end of the topic parts, the subscription can only match if it ends with #
            if i >= len(topic_parts):
                return sub_part == '#'
            
            # If the subscription part is #, it matches the rest of the topic
            if sub_part == '#':
                return True
            
            # If the subscription part is +, it matches any single part
            if sub_part == '+':
                continue
            
            # Otherwise, the parts must match exactly
            if sub_part != topic_parts[i]:
                return False
        
        # If we've checked all subscription parts and haven't returned yet,
        # the subscription matches if it has the same number of parts as the topic
        return len(subscription_parts) == len(topic_parts)
