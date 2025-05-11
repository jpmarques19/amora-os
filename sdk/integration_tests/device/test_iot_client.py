"""
Integration tests for the IoTDeviceClient class.

This module tests the IoT device client which serves as a control layer for Azure IoT Hub
without direct interaction with the player module. The player interaction has been delegated
to the broker module.
"""

import os
import sys
import time
import asyncio
import pytest
import logging
from typing import Dict, Any, List

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the base test class
from integration_tests.base_test import IoTDeviceIntegrationTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestIoTDeviceClient(IoTDeviceIntegrationTest):
    """Integration tests for the IoTDeviceClient class."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connect and disconnect methods."""
        # Connect
        result = await self.iot_client.connect()
        assert result
        assert self.iot_client.connected

        # Disconnect
        await self.iot_client.disconnect()
        assert not self.iot_client.connected

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop methods."""
        # Connect
        result = await self.iot_client.connect()
        assert result

        # Start
        await self.iot_client.start()
        assert self.iot_client.running

        # Wait for telemetry to start
        await asyncio.sleep(2)

        # Stop
        await self.iot_client.stop()
        assert not self.iot_client.running

        # Disconnect
        await self.iot_client.disconnect()

    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test send_message method."""
        # Connect
        result = await self.iot_client.connect()
        assert result

        # Create a message
        from azure.iot.device import Message
        message = Message("Test message")

        # Send the message
        try:
            await self.iot_client.send_message(message)
            # If we get here, the message was sent successfully
            assert True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            assert False

        # Disconnect
        await self.iot_client.disconnect()

    @pytest.mark.asyncio
    async def test_patch_twin_reported_properties(self):
        """Test patch_twin_reported_properties method."""
        # Connect
        result = await self.iot_client.connect()
        assert result

        # Create reported properties
        reported_properties = {
            "test_property": "test_value",
            "timestamp": time.time()
        }

        # Update reported properties
        try:
            await self.iot_client.patch_twin_reported_properties(reported_properties)
            # If we get here, the properties were updated successfully
            assert True
        except Exception as e:
            logger.error(f"Failed to update reported properties: {e}")
            assert False

        # Disconnect
        await self.iot_client.disconnect()

    @pytest.mark.asyncio
    async def test_telemetry(self):
        """Test telemetry."""
        # Connect
        result = await self.iot_client.connect()
        assert result

        # Start
        await self.iot_client.start()

        # Wait for telemetry to be sent
        await asyncio.sleep(5)

        # Stop
        await self.iot_client.stop()

        # Disconnect
        await self.iot_client.disconnect()

        # If we get here without errors, the test passed
        assert True
