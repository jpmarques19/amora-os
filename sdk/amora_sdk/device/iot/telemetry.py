"""
Telemetry module for AmoraSDK Device.

This module handles sending telemetry data to Azure IoT Hub.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

try:
    from azure.iot.device import Message
    IOT_AVAILABLE = True
except ImportError:
    IOT_AVAILABLE = False

logger = logging.getLogger(__name__)

class TelemetryManager:
    """Manages telemetry for the IoT device client."""

    def __init__(self, client, player_interface, interval: int = 60):
        """
        Initialize the telemetry manager.

        Args:
            client: IoT Hub device client
            player_interface: Player interface
            interval (int, optional): Telemetry interval in seconds. Defaults to 60.
        """
        self.client = client
        self.player = player_interface
        self.interval = interval
        self.running = False
        self.task = None

    async def start(self):
        """Start sending telemetry."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._telemetry_loop())

    async def stop(self):
        """Stop sending telemetry."""
        self.running = False

        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        self.task = None

    async def _telemetry_loop(self):
        """Send telemetry periodically."""
        consecutive_errors = 0
        max_consecutive_errors = 3

        while self.running:
            try:
                # Only send telemetry if connected
                if self.client.connected:
                    # Get player status
                    status = self.player.get_status()

                    # Create telemetry message
                    telemetry = {
                        "messageType": "playerStatus",
                        "deviceId": status.get("device_id", "unknown"),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "status": status
                    }

                    # Send telemetry with retry logic
                    retry_count = 0
                    max_retries = 3
                    retry_delay = 2  # seconds

                    while retry_count < max_retries:
                        try:
                            # Create message
                            msg = Message(json.dumps(telemetry))
                            msg.content_type = "application/json"
                            msg.content_encoding = "utf-8"

                            # Send with timeout
                            logger.info(f"Sending telemetry message: {json.dumps(telemetry)}")
                            send_task = asyncio.create_task(self.client.send_message(msg))
                            await asyncio.wait_for(send_task, timeout=10)  # 10 second timeout

                            logger.info(f"Telemetry sent successfully: {json.dumps(telemetry)}")
                            consecutive_errors = 0  # Reset error counter on success
                            break  # Success, exit retry loop
                        except asyncio.TimeoutError:
                            retry_count += 1
                            logger.warning(f"Telemetry send timed out, retry {retry_count}/{max_retries}")
                            await asyncio.sleep(retry_delay)
                        except Exception as send_ex:
                            retry_count += 1
                            logger.warning(f"Error sending telemetry, retry {retry_count}/{max_retries}: {send_ex}")
                            await asyncio.sleep(retry_delay)

                    # If we exhausted all retries
                    if retry_count >= max_retries:
                        consecutive_errors += 1
                        logger.error(f"Failed to send telemetry after {max_retries} retries")

                        # If we have too many consecutive errors, notify the client
                        if consecutive_errors >= max_consecutive_errors:
                            logger.warning(f"Too many consecutive telemetry errors ({consecutive_errors})")
                            await self.client.handle_connection_error()
                            consecutive_errors = 0  # Reset after triggering reconnect
                else:
                    logger.debug("Skipping telemetry - not connected to IoT Hub")

            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")
                consecutive_errors += 1

                # If too many errors, notify the client
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning(f"Too many consecutive errors ({consecutive_errors})")
                    await self.client.handle_connection_error()
                    consecutive_errors = 0  # Reset after triggering reconnect

            # Wait for next telemetry interval
            await asyncio.sleep(self.interval)
