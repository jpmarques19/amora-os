"""
Mock MQTT client for testing.
"""

import json
from typing import Dict, Any, Optional, Callable, List, Tuple, Union


class MockMQTTClient:
    """Mock MQTT client for testing."""
    
    def __init__(self, client_id=None, clean_session=True, userdata=None, protocol=None, transport=None):
        """Initialize the mock MQTT client."""
        self.client_id = client_id
        self.clean_session = clean_session
        self.userdata = userdata
        self.protocol = protocol
        self.transport = transport
        
        self.connected = False
        self.subscriptions = {}
        self.messages = {}
        self.last_will = None
        
        # Callbacks
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_publish = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        
        # Authentication
        self.username = None
        self.password = None
        
        # TLS
        self.tls_config = None
    
    def connect(self, host, port=1883, keepalive=60, bind_address=""):
        """Connect to the broker."""
        self.connected = True
        if self.on_connect:
            self.on_connect(self, self.userdata, {}, 0)
        return 0
    
    def disconnect(self):
        """Disconnect from the broker."""
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect(self, self.userdata, 0)
        return 0
    
    def reconnect(self):
        """Reconnect to the broker."""
        self.connected = True
        if self.on_connect:
            self.on_connect(self, self.userdata, {}, 0)
        return 0
    
    def loop_start(self):
        """Start the network loop."""
        pass
    
    def loop_stop(self, force=False):
        """Stop the network loop."""
        pass
    
    def publish(self, topic, payload=None, qos=0, retain=False, properties=None):
        """Publish a message."""
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Store the message
        if topic not in self.messages:
            self.messages[topic] = []
        self.messages[topic].append((payload, qos, retain, properties))
        
        # Call the on_publish callback
        if self.on_publish:
            self.on_publish(self, self.userdata, 1)  # Use 1 as message ID
        
        # Create a mock result
        class MockMQTTMessageInfo:
            def __init__(self, rc=0):
                self.rc = rc
                self.mid = 1
                self.is_published = True
            
            def wait_for_publish(self):
                return True
        
        return MockMQTTMessageInfo()
    
    def subscribe(self, topic, qos=0, options=None, properties=None):
        """Subscribe to a topic."""
        self.subscriptions[topic] = qos
        
        # Call the on_subscribe callback
        if self.on_subscribe:
            self.on_subscribe(self, self.userdata, 1, [qos])  # Use 1 as message ID
        
        return (0, [qos])  # (MQTT_ERR_SUCCESS, granted_qos)
    
    def unsubscribe(self, topic, properties=None):
        """Unsubscribe from a topic."""
        if topic in self.subscriptions:
            del self.subscriptions[topic]
        
        # Call the on_unsubscribe callback
        if self.on_unsubscribe:
            self.on_unsubscribe(self, self.userdata, 1)  # Use 1 as message ID
        
        return (0,)  # (MQTT_ERR_SUCCESS,)
    
    def username_pw_set(self, username, password=None):
        """Set the username and password."""
        self.username = username
        self.password = password
    
    def tls_set(self, ca_certs=None, certfile=None, keyfile=None, cert_reqs=None,
                tls_version=None, ciphers=None):
        """Set the TLS configuration."""
        self.tls_config = {
            'ca_certs': ca_certs,
            'certfile': certfile,
            'keyfile': keyfile,
            'cert_reqs': cert_reqs,
            'tls_version': tls_version,
            'ciphers': ciphers
        }
    
    def will_set(self, topic, payload=None, qos=0, retain=False, properties=None):
        """Set the last will message."""
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        self.last_will = {
            'topic': topic,
            'payload': payload,
            'qos': qos,
            'retain': retain,
            'properties': properties
        }
    
    def simulate_message(self, topic, payload, qos=0, retain=False, properties=None):
        """Simulate receiving a message."""
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Create a mock message
        class MockMQTTMessage:
            def __init__(self, topic, payload, qos, retain, properties):
                self.topic = topic
                self.payload = payload
                self.qos = qos
                self.retain = retain
                self.properties = properties
                self.mid = 1
                self.timestamp = 0
        
        msg = MockMQTTMessage(topic, payload, qos, retain, properties)
        
        # Call the on_message callback
        if self.on_message:
            self.on_message(self, self.userdata, msg)
    
    def simulate_disconnect(self, rc=0):
        """Simulate a disconnection."""
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect(self, self.userdata, rc)


# Mock MQTT module
class MockMQTT:
    """Mock MQTT module."""
    
    Client = MockMQTTClient
    
    # Error codes
    MQTT_ERR_SUCCESS = 0
    MQTT_ERR_NOMEM = 1
    MQTT_ERR_PROTOCOL = 2
    MQTT_ERR_INVAL = 3
    MQTT_ERR_NO_CONN = 4
    MQTT_ERR_CONN_REFUSED = 5
    MQTT_ERR_NOT_FOUND = 6
    MQTT_ERR_CONN_LOST = 7
    MQTT_ERR_TLS = 8
    MQTT_ERR_PAYLOAD_SIZE = 9
    MQTT_ERR_NOT_SUPPORTED = 10
    MQTT_ERR_AUTH = 11
    MQTT_ERR_ACL_DENIED = 12
    MQTT_ERR_UNKNOWN = 13
    MQTT_ERR_ERRNO = 14
    MQTT_ERR_QUEUE_SIZE = 15
    
    # CONNACK codes
    CONNACK_ACCEPTED = 0
    CONNACK_REFUSED_PROTOCOL_VERSION = 1
    CONNACK_REFUSED_IDENTIFIER_REJECTED = 2
    CONNACK_REFUSED_SERVER_UNAVAILABLE = 3
    CONNACK_REFUSED_BAD_USERNAME_PASSWORD = 4
    CONNACK_REFUSED_NOT_AUTHORIZED = 5
