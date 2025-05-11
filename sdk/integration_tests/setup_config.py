#!/usr/bin/env python3
"""
Setup configuration for integration tests.

This script helps set up the configuration for integration tests.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import configuration
from integration_tests.config import load_config, save_config, CONFIG_FILE_PATH, USER_CONFIG_FILE_PATH

def setup_azure_config(iot_hub_connection_string: Optional[str] = None, 
                       event_hub_connection_string: Optional[str] = None) -> None:
    """
    Set up Azure configuration.
    
    Args:
        iot_hub_connection_string (Optional[str], optional): IoT Hub connection string. Defaults to None.
        event_hub_connection_string (Optional[str], optional): Event Hub connection string. Defaults to None.
    """
    # Load current configuration
    config = load_config()
    
    # Update Azure configuration
    if iot_hub_connection_string:
        config["azure"]["iot_hub_connection_string"] = iot_hub_connection_string
    
    if event_hub_connection_string:
        config["azure"]["event_hub_connection_string"] = event_hub_connection_string
    
    # Save configuration to user config file
    save_config(config, user_config=True)
    
    print(f"Azure configuration saved to {USER_CONFIG_FILE_PATH}")

def setup_mpd_config(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """
    Set up MPD configuration.
    
    Args:
        host (Optional[str], optional): MPD host. Defaults to None.
        port (Optional[int], optional): MPD port. Defaults to None.
    """
    # Load current configuration
    config = load_config()
    
    # Update MPD configuration
    if host:
        config["mpd"]["host"] = host
    
    if port:
        config["mpd"]["port"] = port
    
    # Save configuration to local config file
    save_config(config, user_config=False)
    
    print(f"MPD configuration saved to {CONFIG_FILE_PATH}")

def setup_content_config(storage_path: Optional[str] = None, 
                         playlists_path: Optional[str] = None,
                         default_playlist: Optional[str] = None) -> None:
    """
    Set up content configuration.
    
    Args:
        storage_path (Optional[str], optional): Storage path. Defaults to None.
        playlists_path (Optional[str], optional): Playlists path. Defaults to None.
        default_playlist (Optional[str], optional): Default playlist. Defaults to None.
    """
    # Load current configuration
    config = load_config()
    
    # Update content configuration
    if storage_path:
        config["content"]["storage_path"] = storage_path
    
    if playlists_path:
        config["content"]["playlists_path"] = playlists_path
    
    if default_playlist:
        config["content"]["default_playlist"] = default_playlist
    
    # Save configuration to local config file
    save_config(config, user_config=False)
    
    print(f"Content configuration saved to {CONFIG_FILE_PATH}")

def show_config() -> None:
    """Show current configuration."""
    # Load current configuration
    config = load_config()
    
    # Print configuration
    print("Current configuration:")
    print(json.dumps(config, indent=4))
    
    # Print configuration files
    print(f"\nLocal config file: {CONFIG_FILE_PATH}")
    print(f"User config file: {USER_CONFIG_FILE_PATH}")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup configuration for integration tests")
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Azure configuration
    azure_parser = subparsers.add_parser("azure", help="Set up Azure configuration")
    azure_parser.add_argument("--iot-hub", help="IoT Hub connection string")
    azure_parser.add_argument("--event-hub", help="Event Hub connection string")
    
    # MPD configuration
    mpd_parser = subparsers.add_parser("mpd", help="Set up MPD configuration")
    mpd_parser.add_argument("--host", help="MPD host")
    mpd_parser.add_argument("--port", type=int, help="MPD port")
    
    # Content configuration
    content_parser = subparsers.add_parser("content", help="Set up content configuration")
    content_parser.add_argument("--storage-path", help="Storage path")
    content_parser.add_argument("--playlists-path", help="Playlists path")
    content_parser.add_argument("--default-playlist", help="Default playlist")
    
    # Show configuration
    subparsers.add_parser("show", help="Show current configuration")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command == "azure":
        setup_azure_config(args.iot_hub, args.event_hub)
    elif args.command == "mpd":
        setup_mpd_config(args.host, args.port)
    elif args.command == "content":
        setup_content_config(args.storage_path, args.playlists_path, args.default_playlist)
    elif args.command == "show":
        show_config()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
