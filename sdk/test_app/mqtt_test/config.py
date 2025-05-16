"""
Configuration module for the MQTT test application.

This module handles loading configuration from files and environment variables.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_credentials_file(file_path: str) -> Dict[str, Any]:
    """
    Load credentials from a file.
    
    Args:
        file_path: Path to the credentials file
        
    Returns:
        Dictionary containing the credentials
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in credentials file: {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading credentials file: {e}")
        return {}

def get_mqtt_config(credentials_file: str = "credentials_configs.txt") -> Dict[str, Any]:
    """
    Get MQTT configuration from credentials file or environment variables.
    
    Args:
        credentials_file: Path to the credentials file
        
    Returns:
        Dictionary containing MQTT configuration
    """
    # Try to load from credentials file
    credentials = load_credentials_file(credentials_file)
    mqtt_config = credentials.get("mqtt", {})
    
    # Override with environment variables if available
    if os.environ.get("MQTT_BROKER_URL"):
        mqtt_config["broker_url"] = os.environ.get("MQTT_BROKER_URL")
    if os.environ.get("MQTT_PORT"):
        mqtt_config["port"] = int(os.environ.get("MQTT_PORT"))
    if os.environ.get("MQTT_USERNAME"):
        mqtt_config["username"] = os.environ.get("MQTT_USERNAME")
    if os.environ.get("MQTT_PASSWORD"):
        mqtt_config["password"] = os.environ.get("MQTT_PASSWORD")
    if os.environ.get("MQTT_DEVICE_ID"):
        mqtt_config["device_id"] = os.environ.get("MQTT_DEVICE_ID")
    
    return mqtt_config

def get_player_config(credentials_file: str = "credentials_configs.txt") -> Dict[str, Any]:
    """
    Get player configuration from credentials file or environment variables.
    
    Args:
        credentials_file: Path to the credentials file
        
    Returns:
        Dictionary containing player configuration
    """
    # Try to load from credentials file
    credentials = load_credentials_file(credentials_file)
    player_config = credentials.get("player", {})
    
    # Override with environment variables if available
    if os.environ.get("MPD_HOST"):
        player_config["mpd_host"] = os.environ.get("MPD_HOST")
    if os.environ.get("MPD_PORT"):
        player_config["mpd_port"] = int(os.environ.get("MPD_PORT"))
    
    return player_config
