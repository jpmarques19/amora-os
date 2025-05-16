#!/usr/bin/env python3
"""
Run script for the MQTT Test Application.

This script provides a command-line interface to run either the client or server
component of the MQTT Test Application.
"""

import argparse
import asyncio
import sys
import os
import logging
import json
import curses
from typing import Dict, Any

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the client and server modules
from client.client import MQTTTestClient
from server.server import MQTTTestServer
from config import get_mqtt_config, get_player_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_credentials_file(output_path: str) -> None:
    """
    Create a credentials file template.
    
    Args:
        output_path: Path to save the credentials file
    """
    # Load the template
    template_path = os.path.join(os.path.dirname(__file__), "credentials_template.json")
    try:
        with open(template_path, "r") as f:
            template = json.load(f)
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        return
    
    # Save the template to the output path
    try:
        with open(output_path, "w") as f:
            json.dump(template, f, indent=4)
        print(f"Credentials template saved to {output_path}")
        print("Please edit this file with your MQTT broker and player configuration")
    except Exception as e:
        logger.error(f"Error saving template: {e}")

async def run_client(config_path: str) -> None:
    """
    Run the client component.
    
    Args:
        config_path: Path to the credentials file
    """
    # Load configuration
    mqtt_config = get_mqtt_config(config_path)
    
    # Check if MQTT configuration is valid
    if not mqtt_config.get("broker_url"):
        print("Error: MQTT broker URL not specified")
        print(f"Please edit {config_path} with your MQTT broker configuration")
        print("or set the MQTT_BROKER_URL environment variable")
        return
    
    # Create client
    client = MQTTTestClient(mqtt_config)
    
    # Start client with curses
    await curses.wrapper(client.start)
    
    # Stop client
    await client.stop()

async def run_server(config_path: str) -> None:
    """
    Run the server component.
    
    Args:
        config_path: Path to the credentials file
    """
    # Load configuration
    mqtt_config = get_mqtt_config(config_path)
    player_config = get_player_config(config_path)
    
    # Check if MQTT configuration is valid
    if not mqtt_config.get("broker_url"):
        print("Error: MQTT broker URL not specified")
        print(f"Please edit {config_path} with your MQTT broker configuration")
        print("or set the MQTT_BROKER_URL environment variable")
        return
    
    # Create server
    server = MQTTTestServer(mqtt_config, player_config)
    
    # Start server
    await server.start()
    
    # Keep running until stopped
    try:
        while server.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MQTT Test Application")
    parser.add_argument("component", choices=["client", "server", "init"],
                        help="Component to run (client, server, or init to create credentials file)")
    parser.add_argument("--config", help="Path to credentials file", default="credentials_configs.txt")
    args = parser.parse_args()
    
    # Run the selected component
    if args.component == "client":
        asyncio.run(run_client(args.config))
    elif args.component == "server":
        asyncio.run(run_server(args.config))
    elif args.component == "init":
        create_credentials_file(args.config)

if __name__ == "__main__":
    main()
