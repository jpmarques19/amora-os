"""
Configuration models for the Broker module.
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field


class QoS(Enum):
    """MQTT Quality of Service levels."""
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


@dataclass
class ConnectionOptions:
    """MQTT connection options."""
    use_tls: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    keep_alive: int = 60
    clean_session: bool = True
    reconnect_on_failure: bool = True
    max_reconnect_delay: int = 300  # seconds


@dataclass
class BrokerConfig:
    """Configuration for the Broker module."""
    broker_url: str
    port: int = 8883
    client_id: str = ""
    device_id: str = ""
    topic_prefix: str = "amora/devices"
    connection_options: ConnectionOptions = field(default_factory=ConnectionOptions)
    default_qos: QoS = QoS.AT_LEAST_ONCE
    raw_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BrokerConfig':
        """
        Create a BrokerConfig instance from a dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            BrokerConfig instance
        """
        broker_config = config.get('broker', {})
        device_id = config.get('device', {}).get('id', '')

        connection_options = ConnectionOptions(
            use_tls=broker_config.get('use_tls', True),
            cert_file=broker_config.get('cert_file'),
            key_file=broker_config.get('key_file'),
            ca_file=broker_config.get('ca_file'),
            username=broker_config.get('username'),
            password=broker_config.get('password'),
            keep_alive=broker_config.get('keep_alive', 60),
            clean_session=broker_config.get('clean_session', True),
            reconnect_on_failure=broker_config.get('reconnect_on_failure', True),
            max_reconnect_delay=broker_config.get('max_reconnect_delay', 300)
        )

        return cls(
            broker_url=broker_config.get('broker_url', ''),
            port=broker_config.get('port', 8883),
            client_id=broker_config.get('client_id', f"device-{device_id}"),
            device_id=device_id,
            topic_prefix=broker_config.get('topic_prefix', 'amora/devices'),
            connection_options=connection_options,
            default_qos=QoS(broker_config.get('default_qos', 1)),
            raw_config=config
        )
