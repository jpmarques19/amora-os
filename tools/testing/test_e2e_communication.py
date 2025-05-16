#!/usr/bin/env python3
"""
Amora Music System End-to-End Communication Test

This script tests the end-to-end communication between the device music player
and the MQTT broker by sending commands and verifying responses.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: Paho MQTT client not installed. Please install it with:")
    print("  pip install paho-mqtt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
client = None
connected = False
command_responses = {}
device_state = {}
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
}


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    global connected
    if rc == 0:
        logger.info("Connected to MQTT broker")
        connected = True
        
        # Subscribe to topics
        device_id = userdata.get("device_id", "amora-test-device")
        topic_prefix = userdata.get("topic_prefix", "amora/devices")
        
        # Subscribe to state updates
        state_topic = f"{topic_prefix}/{device_id}/state"
        client.subscribe(state_topic)
        logger.info(f"Subscribed to state topic: {state_topic}")
        
        # Subscribe to command responses
        response_topic = f"{topic_prefix}/{device_id}/response"
        client.subscribe(response_topic)
        logger.info(f"Subscribed to response topic: {response_topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        device_id = userdata.get("device_id", "amora-test-device")
        topic_prefix = userdata.get("topic_prefix", "amora/devices")
        
        # Handle state updates
        if topic == f"{topic_prefix}/{device_id}/state":
            global device_state
            device_state = payload
            logger.debug(f"Received state update: {json.dumps(payload, indent=2)}")
        
        # Handle command responses
        elif topic == f"{topic_prefix}/{device_id}/response":
            if "command_id" in payload:
                command_id = payload["command_id"]
                command_responses[command_id] = payload
                logger.debug(f"Received response for command {command_id}: {json.dumps(payload, indent=2)}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def send_command(command: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Send a command to the device and wait for a response.
    
    Args:
        command: Command name
        params: Command parameters
        
    Returns:
        Command response or None if no response received
    """
    global client, command_responses
    
    if not connected:
        logger.error("Not connected to MQTT broker")
        return None
    
    # Generate a command ID
    command_id = f"{command}-{int(time.time())}"
    
    # Create command message
    command_msg = {
        "command": command,
        "command_id": command_id,
        "params": params or {}
    }
    
    # Get device ID and topic prefix from userdata
    userdata = client._userdata
    device_id = userdata.get("device_id", "amora-test-device")
    topic_prefix = userdata.get("topic_prefix", "amora/devices")
    
    # Publish command
    command_topic = f"{topic_prefix}/{device_id}/command"
    client.publish(command_topic, json.dumps(command_msg))
    logger.info(f"Sent command: {command} (ID: {command_id})")
    
    # Wait for response
    start_time = time.time()
    timeout = 5.0  # seconds
    
    while time.time() - start_time < timeout:
        if command_id in command_responses:
            response = command_responses[command_id]
            del command_responses[command_id]
            return response
        time.sleep(0.1)
    
    logger.warning(f"No response received for command: {command} (ID: {command_id})")
    return None


def run_test(name: str, command: str, params: Optional[Dict[str, Any]] = None, 
             expected_result: bool = True, check_state: bool = False,
             state_check_fn: Optional[callable] = None) -> bool:
    """
    Run a test by sending a command and verifying the response.
    
    Args:
        name: Test name
        command: Command to send
        params: Command parameters
        expected_result: Expected result value in the response
        check_state: Whether to check the device state after the command
        state_check_fn: Function to check the device state
        
    Returns:
        True if the test passed, False otherwise
    """
    global test_results
    
    logger.info(f"Running test: {name}")
    test_results["total"] += 1
    
    # Send the command
    response = send_command(command, params)
    
    # Check if we got a response
    if response is None:
        logger.error(f"Test failed: {name} - No response received")
        test_results["failed"] += 1
        return False
    
    # Check if the result matches the expected result
    result = response.get("result", False)
    if result != expected_result:
        logger.error(f"Test failed: {name} - Expected result {expected_result}, got {result}")
        logger.error(f"Response: {json.dumps(response, indent=2)}")
        test_results["failed"] += 1
        return False
    
    # Check the device state if requested
    if check_state and state_check_fn:
        # Wait a moment for the state to update
        time.sleep(1.0)
        
        # Check the state
        if not state_check_fn(device_state):
            logger.error(f"Test failed: {name} - State check failed")
            logger.error(f"Current state: {json.dumps(device_state, indent=2)}")
            test_results["failed"] += 1
            return False
    
    logger.info(f"Test passed: {name}")
    test_results["passed"] += 1
    return True


def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Amora Music System End-to-End Communication Test")
    parser.add_argument("-b", "--broker-host", default="localhost", help="MQTT broker hostname")
    parser.add_argument("-p", "--broker-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("-d", "--device-id", default="amora-test-device", help="Device ID")
    parser.add_argument("-t", "--topic-prefix", default="amora/devices", help="Topic prefix")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create MQTT client
    global client
    client = mqtt.Client()
    
    # Set user data
    client._userdata = {
        "device_id": args.device_id,
        "topic_prefix": args.topic_prefix
    }
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {args.broker_host}:{args.broker_port}")
        client.connect(args.broker_host, args.broker_port)
        
        # Start the MQTT loop
        client.loop_start()
        
        # Wait for connection
        timeout = 5.0  # seconds
        start_time = time.time()
        while not connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not connected:
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Wait for initial state
        logger.info("Waiting for initial device state...")
        time.sleep(2.0)
        
        # Run tests
        logger.info("Starting tests...")
        
        # Test 1: Get status
        run_test(
            name="Get Status",
            command="get_status",
            expected_result=True
        )
        
        # Test 2: Set volume
        run_test(
            name="Set Volume",
            command="set_volume",
            params={"volume": 50},
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("volume", 0) == 50
        )
        
        # Test 3: Get playlists
        run_test(
            name="Get Playlists",
            command="get_playlists",
            expected_result=True
        )
        
        # Test 4: Play
        run_test(
            name="Play",
            command="play",
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("state") == "play"
        )
        
        # Test 5: Pause
        run_test(
            name="Pause",
            command="pause",
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("state") == "pause"
        )
        
        # Test 6: Stop
        run_test(
            name="Stop",
            command="stop",
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("state") == "stop"
        )
        
        # Test 7: Set repeat
        run_test(
            name="Set Repeat",
            command="set_repeat",
            params={"repeat": True},
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("repeat", False) is True
        )
        
        # Test 8: Set random
        run_test(
            name="Set Random",
            command="set_random",
            params={"random": True},
            expected_result=True,
            check_state=True,
            state_check_fn=lambda state: state.get("random", False) is True
        )
        
        # Print test results
        logger.info("Test results:")
        logger.info(f"  Total: {test_results['total']}")
        logger.info(f"  Passed: {test_results['passed']}")
        logger.info(f"  Failed: {test_results['failed']}")
        logger.info(f"  Skipped: {test_results['skipped']}")
        
        # Return success if all tests passed
        return 0 if test_results["failed"] == 0 else 1
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    
    finally:
        # Clean up
        if client:
            client.loop_stop()
            client.disconnect()


if __name__ == "__main__":
    sys.exit(main())
