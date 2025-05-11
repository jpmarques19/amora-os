"""
Configuration module for integration tests.

This module loads configuration from environment variables or a local config file.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "azure": {
        "iot_hub_connection_string": "",
        "event_hub_connection_string": ""
    },
    "mpd": {
        "host": "localhost",
        "port": 6600
    },
    "content": {
        "storage_path": "/tmp/amora_test/music",
        "playlists_path": "/tmp/amora_test/playlists",
        "default_playlist": "default"
    },
    "audio": {
        "backend": "pipewire",
        "device": "default",
        "volume": 80
    },
    "dev_mode": True
}

# Path to local config file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")
# Path to user config file (for sensitive data like connection strings)
USER_CONFIG_FILE_PATH = os.path.expanduser("~/.amora/integration_test_config.json")

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or config files.

    The configuration is loaded in the following order (later sources override earlier ones):
    1. Default configuration
    2. Local config file (integration_tests/config.json)
    3. User config file (~/.amora/integration_test_config.json)
    4. Environment variables

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Try to load from local config file
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r") as f:
                file_config = json.load(f)
                _deep_update(config, file_config)
                logger.info(f"Loaded configuration from {CONFIG_FILE_PATH}")
    except Exception as e:
        logger.warning(f"Failed to load configuration from local file: {e}")

    # Try to load from user config file (for sensitive data)
    try:
        if os.path.exists(USER_CONFIG_FILE_PATH):
            with open(USER_CONFIG_FILE_PATH, "r") as f:
                user_config = json.load(f)
                _deep_update(config, user_config)
                logger.info(f"Loaded user configuration from {USER_CONFIG_FILE_PATH}")
    except Exception as e:
        logger.warning(f"Failed to load configuration from user file: {e}")

    # Override with environment variables
    # Azure IoT Hub connection string
    if os.environ.get("AMORA_IOT_HUB_CONNECTION_STRING"):
        config["azure"]["iot_hub_connection_string"] = os.environ.get("AMORA_IOT_HUB_CONNECTION_STRING")

    # Azure Event Hub connection string
    if os.environ.get("AMORA_EVENT_HUB_CONNECTION_STRING"):
        config["azure"]["event_hub_connection_string"] = os.environ.get("AMORA_EVENT_HUB_CONNECTION_STRING")

    # MPD host
    if os.environ.get("AMORA_MPD_HOST"):
        config["mpd"]["host"] = os.environ.get("AMORA_MPD_HOST")

    # MPD port
    if os.environ.get("AMORA_MPD_PORT"):
        try:
            config["mpd"]["port"] = int(os.environ.get("AMORA_MPD_PORT"))
        except ValueError:
            logger.warning(f"Invalid MPD port: {os.environ.get('AMORA_MPD_PORT')}")

    # Content storage path
    if os.environ.get("AMORA_CONTENT_STORAGE_PATH"):
        config["content"]["storage_path"] = os.environ.get("AMORA_CONTENT_STORAGE_PATH")

    # Content playlists path
    if os.environ.get("AMORA_CONTENT_PLAYLISTS_PATH"):
        config["content"]["playlists_path"] = os.environ.get("AMORA_CONTENT_PLAYLISTS_PATH")

    return config

def save_config(config: Dict[str, Any], user_config: bool = True) -> bool:
    """
    Save configuration to config file.

    Args:
        config (Dict[str, Any]): Configuration dictionary
        user_config (bool, optional): Whether to save to user config file. Defaults to True.

    Returns:
        bool: True if successful, False otherwise
    """
    # Determine which file to save to
    file_path = USER_CONFIG_FILE_PATH if user_config else CONFIG_FILE_PATH

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save config
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)

        logger.info(f"Saved configuration to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False

def _deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Deep update a nested dictionary.

    Args:
        target (Dict[str, Any]): Target dictionary to update
        source (Dict[str, Any]): Source dictionary with new values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value

def create_test_directories() -> None:
    """Create directories needed for tests."""
    config = load_config()

    # Create music directory
    os.makedirs(config["content"]["storage_path"], exist_ok=True)

    # Create playlists directory
    os.makedirs(config["content"]["playlists_path"], exist_ok=True)

    logger.info(f"Created test directories: {config['content']['storage_path']} and {config['content']['playlists_path']}")

def cleanup_test_directories() -> None:
    """Clean up test directories."""
    config = load_config()

    # Only remove directories if they are in /tmp to avoid accidental deletion
    if config["content"]["storage_path"].startswith("/tmp"):
        try:
            import shutil
            shutil.rmtree(config["content"]["storage_path"], ignore_errors=True)
            logger.info(f"Removed test directory: {config['content']['storage_path']}")
        except Exception as e:
            logger.warning(f"Failed to remove test directory: {e}")

    if config["content"]["playlists_path"].startswith("/tmp"):
        try:
            import shutil
            shutil.rmtree(config["content"]["playlists_path"], ignore_errors=True)
            logger.info(f"Removed test directory: {config['content']['playlists_path']}")
        except Exception as e:
            logger.warning(f"Failed to remove test directory: {e}")
