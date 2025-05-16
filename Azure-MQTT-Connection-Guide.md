# Azure MQTT Connection Guide

This document provides detailed configuration information for connecting to Azure IoT Hub using the MQTT protocol, including connection string formats, authentication methods, client configuration parameters, and security best practices.

## Connection String Formats

Azure IoT Hub uses connection strings to authenticate devices. The connection string format varies depending on the authentication method used.

### Device Connection String Format

```
HostName={IoTHubName}.azure-devices.net;DeviceId={DeviceId};SharedAccessKey={SharedAccessKey}
```

### Example Connection Strings

**SAS Token Authentication:**
```
HostName=myiothub.azure-devices.net;DeviceId=mydevice;SharedAccessKey=abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGH=
```

**X.509 Certificate Authentication:**
```
HostName=myiothub.azure-devices.net;DeviceId=mydevice;x509=true
```

## Authentication Methods

Azure IoT Hub supports two primary authentication methods for MQTT connections:

### 1. SAS Token Authentication

Shared Access Signature (SAS) tokens provide a secure way to authenticate devices without sending the primary key over the network.

#### SAS Token Format

```
SharedAccessSignature sig={signature}&se={expiry}&sr={resourceURI}&skn={policyName}
```

Where:
- `{signature}`: HMAC-SHA256 signature string (Base64 encoded)
- `{expiry}`: Token expiration time in seconds since epoch (1970-01-01T00:00:00Z)
- `{resourceURI}`: URI of the resource being accessed
- `{policyName}`: Name of the shared access policy (optional for device tokens)

#### Generating SAS Tokens in Code

```python
import base64
import hmac
import hashlib
import time
import urllib.parse

def generate_sas_token(uri, key, policy_name=None, expiry=3600):
    """
    Generate a SAS token for Azure IoT Hub
    
    :param uri: Resource URI (e.g., myiothub.azure-devices.net/devices/mydevice)
    :param key: Shared access key
    :param policy_name: Name of the shared access policy (optional)
    :param expiry: Token expiration time in seconds (default: 1 hour)
    :return: SAS token string
    """
    ttl = int(time.time()) + expiry
    sign_key = "%s\n%d" % (urllib.parse.quote_plus(uri), ttl)
    signature = base64.b64encode(
        hmac.HMAC(
            base64.b64decode(key), 
            sign_key.encode('utf-8'), 
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    token = {
        'sr': uri,
        'sig': signature,
        'se': str(ttl)
    }
    
    if policy_name:
        token['skn'] = policy_name
        
    return 'SharedAccessSignature ' + urllib.parse.urlencode(token)
```

### 2. X.509 Certificate Authentication

X.509 certificates provide a more secure authentication method than SAS tokens and are recommended for production environments.

#### Certificate Requirements

- Certificates must be in PEM format (.pem, .crt, or .cer files)
- Private keys must be in PEM format (.pem or .key files)
- Certificate chain must be properly configured
- Device ID must match the Common Name (CN) in the certificate subject

#### Using X.509 Certificates in Code

```python
import ssl
import paho.mqtt.client as mqtt

def connect_with_certificate(device_id, hostname, cert_file, key_file):
    """
    Connect to Azure IoT Hub using X.509 certificate authentication
    
    :param device_id: Device ID registered in IoT Hub
    :param hostname: IoT Hub hostname (e.g., myiothub.azure-devices.net)
    :param cert_file: Path to the certificate file (.pem, .crt, or .cer)
    :param key_file: Path to the private key file (.pem or .key)
    :return: MQTT client instance
    """
    client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)
    
    # Configure TLS with certificate authentication
    client.tls_set(
        ca_certs=None,  # Use system CA certificates
        certfile=cert_file,
        keyfile=key_file,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )
    
    # Connect to IoT Hub
    client.connect(hostname, port=8883, keepalive=60)
    
    return client
```

## Client Configuration Parameters

When connecting to Azure IoT Hub using MQTT, the following configuration parameters are essential:

### Required Parameters

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `client_id` | Device identifier | N/A | Use the registered device ID |
| `hostname` | IoT Hub hostname | N/A | `{iothubname}.azure-devices.net` |
| `port` | MQTT port | 8883 | 8883 (TLS) |
| `protocol` | MQTT protocol version | N/A | MQTT v3.1.1 |
| `keepalive` | Keep-alive interval in seconds | 60 | 60-300 |
| `clean_session` | Whether to start a clean session | True | True for most cases |

### Optional Parameters

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `username` | MQTT username | N/A | `{iothubname}.azure-devices.net/{deviceId}/?api-version=2021-04-12` |
| `password` | MQTT password | N/A | SAS token (if using SAS authentication) |
| `reconnect_delay` | Reconnection delay in seconds | Varies | Exponential backoff (1-30s) |
| `max_inflight_messages` | Max in-flight messages | 20 | 10-20 |
| `retry_interval` | Message retry interval | Varies | 5-60s |
| `qos` | Quality of Service level | 0 | 1 for important messages |

### Example Client Configuration

```python
import paho.mqtt.client as mqtt
import ssl

# Configuration parameters
config = {
    'client_id': 'mydevice',
    'hostname': 'myiothub.azure-devices.net',
    'port': 8883,
    'username': 'myiothub.azure-devices.net/mydevice/?api-version=2021-04-12',
    'password': 'SharedAccessSignature sr=...',  # SAS token
    'keepalive': 120,
    'clean_session': True,
    'qos': 1
}

# Create MQTT client
client = mqtt.Client(client_id=config['client_id'], protocol=mqtt.MQTTv311)
client.username_pw_set(config['username'], config['password'])

# Configure TLS
client.tls_set(
    ca_certs=None,  # Use system CA certificates
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)

# Connect to IoT Hub
client.connect(config['hostname'], config['port'], config['keepalive'])
```

## MQTT Topic Structure

Azure IoT Hub uses a specific topic structure for device communication:

### Device-to-Cloud Messages

```
devices/{device_id}/messages/events/
```

With optional properties:
```
devices/{device_id}/messages/events/{property_bag}
```

Where `{property_bag}` is a set of key-value pairs in the format: `key1=value1&key2=value2`

### Cloud-to-Device Messages

Subscribe to:
```
devices/{device_id}/messages/devicebound/#
```

### Direct Methods

Subscribe to:
```
$iothub/methods/POST/#
```

Respond to:
```
$iothub/methods/res/{status}/?$rid={request_id}
```

### Device Twin

Get twin:
```
$iothub/twin/GET/?$rid={request_id}
```

Receive twin updates:
```
$iothub/twin/PATCH/properties/desired/#
```

Report properties:
```
$iothub/twin/PATCH/properties/reported/?$rid={request_id}
```

## Security Best Practices

### Connection Security

1. **Always use TLS/SSL**: Connect to Azure IoT Hub only over TLS (port 8883) to ensure encrypted communication.

2. **Validate Server Certificates**: Always validate the server's TLS certificate against trusted certificate authorities.

3. **Use X.509 Certificates**: For production environments, use X.509 certificate authentication instead of SAS tokens.

4. **Rotate Credentials Regularly**: Implement a credential rotation strategy, especially for SAS tokens.

5. **Use Short-lived SAS Tokens**: If using SAS tokens, keep their lifetime short (1-24 hours) and refresh them before expiry.

### Device Security

1. **Secure Storage of Credentials**: Store device credentials (private keys, SAS tokens) in secure storage, preferably in hardware security modules (HSM) or trusted platform modules (TPM).

2. **Implement Device Attestation**: Use Azure IoT Hub Device Provisioning Service (DPS) for secure device attestation.

3. **Use Unique Credentials**: Each device should have unique credentials; never share credentials across devices.

4. **Implement IP Filtering**: Configure IoT Hub IP filtering to allow connections only from expected IP ranges.

5. **Monitor for Anomalies**: Implement monitoring for unusual connection patterns or message volumes.

### Message Security

1. **Use QoS 1 for Important Messages**: For critical messages, use QoS 1 to ensure delivery.

2. **Implement Message Encryption**: For sensitive data, implement application-level encryption of message payloads.

3. **Validate Message Integrity**: Use message signatures or HMACs to verify message integrity.

4. **Implement Rate Limiting**: Protect against DoS attacks by implementing rate limiting in your device code.

5. **Use Message IDs**: Include unique message IDs to detect duplicates and ensure idempotent processing.

## Potential Vulnerabilities and Mitigations

| Vulnerability | Mitigation |
|---------------|------------|
| Credential Theft | Store credentials securely, use X.509 certificates, implement credential rotation |
| Man-in-the-Middle Attacks | Always use TLS, validate server certificates, implement certificate pinning |
| Replay Attacks | Use message timestamps and nonces, implement message expiration |
| Denial of Service | Implement rate limiting, use throttling policies in IoT Hub |
| Unauthorized Access | Implement proper authentication, use IP filtering, follow principle of least privilege |
| Data Leakage | Encrypt sensitive data at rest and in transit, implement proper access controls |

By following these guidelines and best practices, you can establish a secure and reliable connection between your devices and Azure IoT Hub using the MQTT protocol.
