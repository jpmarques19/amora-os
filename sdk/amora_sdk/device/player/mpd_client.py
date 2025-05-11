"""
MPD Client wrapper for AmoraSDK Device.

Provides a wrapper around the MPD client with error handling and reconnection logic.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from mpd import MPDClient

logger = logging.getLogger(__name__)

class MPDClientWrapper:
    """Wrapper around MPDClient with error handling and reconnection logic."""
    
    def __init__(self, host: str = "localhost", port: int = 6600, timeout: int = 10):
        """
        Initialize the MPD client wrapper.
        
        Args:
            host (str, optional): MPD server host. Defaults to "localhost".
            port (int, optional): MPD server port. Defaults to 6600.
            timeout (int, optional): Connection timeout in seconds. Defaults to 10.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = MPDClient()
        self.client.timeout = timeout
        self.connected = False
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def connect(self) -> bool:
        """
        Connect to MPD server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.connected:
            return True
            
        try:
            self.client.connect(self.host, self.port)
            self.connected = True
            logger.debug(f"Connected to MPD server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MPD server: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MPD server."""
        if not self.connected:
            return
            
        try:
            self.client.close()
            self.client.disconnect()
            logger.debug("Disconnected from MPD server")
        except Exception as e:
            logger.error(f"Error disconnecting from MPD server: {e}")
        finally:
            self.connected = False
    
    def reconnect(self) -> bool:
        """
        Reconnect to MPD server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.disconnect()
        return self.connect()
    
    def _ensure_connected(self) -> bool:
        """
        Ensure connection to MPD server.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected:
            return self.connect()
        
        try:
            # Test connection with a simple command
            self.client.ping()
            return True
        except Exception:
            logger.warning("MPD connection lost, reconnecting...")
            return self.reconnect()
    
    def _execute_command(self, command: str, *args, **kwargs) -> Any:
        """
        Execute an MPD command with error handling and retries.
        
        Args:
            command (str): Command to execute
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            Any: Command result
            
        Raises:
            Exception: If command execution fails after retries
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            if not self._ensure_connected():
                retries += 1
                time.sleep(self.retry_delay)
                continue
                
            try:
                # Get the command method
                cmd_method = getattr(self.client, command)
                
                # Execute the command
                result = cmd_method(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Error executing MPD command {command}: {e}")
                retries += 1
                
                if retries < self.max_retries:
                    logger.debug(f"Retrying command {command} ({retries}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                    self.reconnect()
        
        # If we get here, all retries failed
        logger.error(f"Failed to execute MPD command {command} after {self.max_retries} retries")
        raise last_error if last_error else Exception(f"Failed to execute MPD command {command}")
    
    def __getattr__(self, name: str) -> Callable:
        """
        Handle attribute access for MPD commands.
        
        Args:
            name (str): Attribute name
            
        Returns:
            Callable: Function that executes the MPD command
        """
        # Check if the attribute exists in the MPD client
        if not hasattr(self.client, name):
            raise AttributeError(f"MPDClientWrapper has no attribute '{name}'")
            
        # Return a function that executes the command
        def command_wrapper(*args, **kwargs):
            return self._execute_command(name, *args, **kwargs)
            
        return command_wrapper
