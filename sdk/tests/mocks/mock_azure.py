"""
Mock Azure IoT SDK for testing.
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional, List

class MockMessage:
    """Mock Message class for testing."""
    
    def __init__(self, data: str):
        """
        Initialize the mock message.
        
        Args:
            data (str): Message data
        """
        self.data = data
        self.content_type = None
        self.content_encoding = None
        self.custom_properties = {}
        
    def get_data(self) -> str:
        """
        Get message data.
        
        Returns:
            str: Message data
        """
        return self.data

class MockMethodRequest:
    """Mock MethodRequest class for testing."""
    
    def __init__(self, method_name: str, payload: Any = None, request_id: str = "1"):
        """
        Initialize the mock method request.
        
        Args:
            method_name (str): Method name
            payload (Any, optional): Method payload. Defaults to None.
            request_id (str, optional): Request ID. Defaults to "1".
        """
        self.name = method_name
        self.payload = payload
        self.request_id = request_id

class MockMethodResponse:
    """Mock MethodResponse class for testing."""
    
    def __init__(self, request_id: str, status: int, payload: Any = None):
        """
        Initialize the mock method response.
        
        Args:
            request_id (str): Request ID
            status (int): Status code
            payload (Any, optional): Response payload. Defaults to None.
        """
        self.request_id = request_id
        self.status = status
        self.payload = payload
    
    @classmethod
    def create_from_method_request(cls, method_request, status, payload=None):
        """
        Create a method response from a method request.
        
        Args:
            method_request: Method request
            status (int): Status code
            payload (Any, optional): Response payload. Defaults to None.
            
        Returns:
            MockMethodResponse: Method response
        """
        return cls(method_request.request_id, status, payload)

class MockIoTHubDeviceClient:
    """Mock IoTHubDeviceClient class for testing."""
    
    def __init__(self):
        """Initialize the mock IoT Hub device client."""
        self.connected = False
        self.on_connection_state_change = None
        self.on_method_request_received = None
        self.on_twin_desired_properties_patch_received = None
        self.reported_properties = {}
        self.desired_properties = {}
        self.sent_messages = []
        self.method_responses = []
        
    @classmethod
    def create_from_connection_string(cls, connection_string, **kwargs):
        """
        Create a client from a connection string.
        
        Args:
            connection_string (str): Connection string
            **kwargs: Additional arguments
            
        Returns:
            MockIoTHubDeviceClient: Client instance
        """
        return cls()
        
    async def connect(self):
        """Connect to IoT Hub."""
        self.connected = True
        if self.on_connection_state_change:
            self.on_connection_state_change(True)
        
    async def disconnect(self):
        """Disconnect from IoT Hub."""
        self.connected = False
        if self.on_connection_state_change:
            self.on_connection_state_change(False)
        
    async def send_message(self, message):
        """
        Send a message to IoT Hub.
        
        Args:
            message: Message to send
        """
        self.sent_messages.append(message)
        
    async def patch_twin_reported_properties(self, reported_properties):
        """
        Update reported properties.
        
        Args:
            reported_properties (Dict[str, Any]): Reported properties
        """
        self.reported_properties.update(reported_properties)
        
    async def send_method_response(self, method_response):
        """
        Send a method response.
        
        Args:
            method_response: Method response
        """
        self.method_responses.append(method_response)
        
    def simulate_method_request(self, method_name: str, payload: Any = None):
        """
        Simulate a method request.
        
        Args:
            method_name (str): Method name
            payload (Any, optional): Method payload. Defaults to None.
            
        Returns:
            bool: True if the method was handled, False otherwise
        """
        if self.on_method_request_received:
            request = MockMethodRequest(method_name, payload)
            asyncio.create_task(self.on_method_request_received(request))
            return True
        return False
        
    def simulate_desired_properties_update(self, properties: Dict[str, Any]):
        """
        Simulate a desired properties update.
        
        Args:
            properties (Dict[str, Any]): Desired properties
            
        Returns:
            bool: True if the update was handled, False otherwise
        """
        if self.on_twin_desired_properties_patch_received:
            self.desired_properties.update(properties)
            asyncio.create_task(self.on_twin_desired_properties_patch_received(properties))
            return True
        return False
        
    def simulate_connection_state_change(self, connected: bool):
        """
        Simulate a connection state change.
        
        Args:
            connected (bool): Connection state
            
        Returns:
            bool: True if the change was handled, False otherwise
        """
        if self.on_connection_state_change:
            self.connected = connected
            self.on_connection_state_change(connected)
            return True
        return False
