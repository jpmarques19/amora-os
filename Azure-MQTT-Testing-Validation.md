# Azure MQTT Testing and Validation Guide

This document provides detailed procedures for verifying successful connections to Azure IoT Hub using MQTT, methods for monitoring message flow, and a comprehensive troubleshooting section with common errors and solutions.

## Verifying Successful Connections

### Connection Verification Procedure

1. **Basic Connection Test**

   Use the following Python script to test basic connectivity to Azure IoT Hub:

   ```python
   import os
   import time
   from azure.iot.device import IoTHubDeviceClient

   # Connection string format: "HostName=<iothub_host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
   CONNECTION_STRING = "HostName=your-iothub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key"

   def test_connection():
       try:
           # Create client
           client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
           
           # Connect to IoT Hub
           print("Connecting to IoT Hub...")
           client.connect()
           print("Connected successfully!")
           
           # Wait a moment
           time.sleep(5)
           
           # Disconnect
           client.disconnect()
           print("Disconnected")
           return True
       except Exception as e:
           print(f"Connection failed: {e}")
           return False

   if __name__ == "__main__":
       test_connection()
   ```

2. **Message Sending Test**

   Extend the basic test to send a test message:

   ```python
   import json
   from azure.iot.device import Message

   def test_message_sending():
       try:
           # Create client
           client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
           
           # Connect to IoT Hub
           print("Connecting to IoT Hub...")
           client.connect()
           print("Connected successfully!")
           
           # Create and send test message
           test_message = {
               "message_type": "test",
               "device_id": client.device_id,
               "timestamp": time.time(),
               "test_value": 42
           }
           
           msg = Message(json.dumps(test_message))
           msg.content_type = "application/json"
           msg.content_encoding = "utf-8"
           
           print("Sending test message...")
           client.send_message(msg)
           print("Test message sent successfully!")
           
           # Disconnect
           client.disconnect()
           print("Disconnected")
           return True
       except Exception as e:
           print(f"Test failed: {e}")
           return False
   ```

3. **Message Receiving Test**

   Test receiving cloud-to-device messages:

   ```python
   def test_message_receiving():
       try:
           # Create client
           client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
           
           # Set message received handler
           def message_handler(message):
               print("Message received:")
               print(f"Data: {message.data.decode('utf-8')}")
               print(f"Properties: {message.custom_properties}")
               return IoTHubMessageDispositionResult.ACCEPTED
           
           client.on_message_received = message_handler
           
           # Connect to IoT Hub
           print("Connecting to IoT Hub...")
           client.connect()
           print("Connected successfully!")
           print("Waiting for messages... (Press Ctrl+C to exit)")
           
           # Wait for messages
           try:
               while True:
                   time.sleep(1)
           except KeyboardInterrupt:
               pass
           
           # Disconnect
           client.disconnect()
           print("Disconnected")
           return True
       except Exception as e:
           print(f"Test failed: {e}")
           return False
   ```

### Expected Logs and Outputs

When a connection is successful, you should see logs similar to the following:

1. **Successful Connection Logs**

   ```
   Connecting to IoT Hub...
   Connected successfully!
   Disconnected
   ```

2. **Successful Message Sending Logs**

   ```
   Connecting to IoT Hub...
   Connected successfully!
   Sending test message...
   Test message sent successfully!
   Disconnected
   ```

3. **Successful Message Receiving Logs**

   ```
   Connecting to IoT Hub...
   Connected successfully!
   Waiting for messages... (Press Ctrl+C to exit)
   Message received:
   Data: {"command": "test_command", "parameter": "test_value"}
   Properties: {'message_id': '12345', 'correlation_id': '67890'}
   Disconnected
   ```

### Connection Verification Using MQTT Client Tools

You can also use standard MQTT client tools to verify connectivity:

1. **Using Mosquitto Client**

   ```bash
   # Install Mosquitto clients
   sudo apt-get install mosquitto-clients
   
   # Generate SAS token (use the script from the Connection Guide)
   SAS_TOKEN=$(python generate_sas_token.py)
   
   # Connect to IoT Hub using Mosquitto
   mosquitto_sub \
     -h your-iothub.azure-devices.net \
     -p 8883 \
     -i your-device-id \
     -u "your-iothub.azure-devices.net/your-device-id/?api-version=2021-04-12" \
     -P "$SAS_TOKEN" \
     -t "devices/your-device-id/messages/devicebound/#" \
     --cafile /etc/ssl/certs/ca-certificates.crt \
     -v
   ```

2. **Using MQTT Explorer**

   - Download and install [MQTT Explorer](http://mqtt-explorer.com/)
   - Configure connection:
     - Host: your-iothub.azure-devices.net
     - Port: 8883
     - Protocol: mqtt/tls
     - Client ID: your-device-id
     - Username: your-iothub.azure-devices.net/your-device-id/?api-version=2021-04-12
     - Password: SAS token
     - SSL/TLS: Enabled
   - Connect and subscribe to `devices/your-device-id/messages/devicebound/#`

## Monitoring Message Flow in Azure

### Azure Portal Monitoring

1. **IoT Hub Metrics**
   - Navigate to your IoT Hub in the Azure Portal
   - Select "Metrics" from the left menu
   - Add metrics to monitor:
     - "Total number of messages used"
     - "Connected devices"
     - "Telemetry message send attempts"
     - "Routing: messages delivered to fallback endpoint"

2. **IoT Hub Message Routing**
   - Navigate to "Message routing" in your IoT Hub
   - Check the message counts for each endpoint
   - Verify that messages are being delivered to the expected endpoints

3. **Device Explorer**
   - Navigate to "Devices" in your IoT Hub
   - Select a specific device to view its details
   - Check the "Device Twin" for reported properties
   - Use "Direct Method" to test device responsiveness

### Azure Monitor and Log Analytics

1. **Setting Up Diagnostic Logs**
   - Navigate to your IoT Hub
   - Select "Diagnostic settings" from the left menu
   - Create a new diagnostic setting:
     - Name: "IoTHubLogs"
     - Categories: Select "Connections", "Device Telemetry", "Cloud to Device Commands", "Twin Operations"
     - Destination: Send to Log Analytics Workspace

2. **Querying Logs in Log Analytics**
   - Navigate to your Log Analytics workspace
   - Use the following sample queries:

   **Check device connections:**
   ```kusto
   AzureDiagnostics
   | where ResourceProvider == "MICROSOFT.DEVICES" and ResourceType == "IOTHUBS"
   | where Category == "Connections"
   | project TimeGenerated, OperationName, Level, ResultType, ResultDescription, DeviceId
   | order by TimeGenerated desc
   ```

   **Check telemetry messages:**
   ```kusto
   AzureDiagnostics
   | where ResourceProvider == "MICROSOFT.DEVICES" and ResourceType == "IOTHUBS"
   | where Category == "DeviceTelemetry"
   | project TimeGenerated, OperationName, Level, ResultType, ResultDescription, DeviceId
   | order by TimeGenerated desc
   ```

3. **Creating Custom Dashboards**
   - In Azure Portal, navigate to "Dashboard"
   - Create a new dashboard
   - Add tiles for IoT Hub metrics and Log Analytics queries

### Azure CLI Monitoring

Use Azure CLI to monitor IoT Hub activity:

```bash
# Get device connection state
az iot hub device-identity show \
  --hub-name your-iothub \
  --device-id your-device-id \
  --query connectionState

# Monitor device-to-cloud events
az iot hub monitor-events \
  --hub-name your-iothub \
  --device-id your-device-id \
  --timeout 30

# Get IoT Hub metrics
az monitor metrics list \
  --resource your-iothub \
  --resource-group your-resource-group \
  --resource-type "Microsoft.Devices/IotHubs" \
  --metric "d2c.telemetry.ingress.success" \
  --interval PT1H
```

### Recommended Monitoring Tools

1. **Azure IoT Explorer**
   - Download from [GitHub](https://github.com/Azure/azure-iot-explorer/releases)
   - Connect using IoT Hub connection string
   - Monitor device telemetry, properties, and methods

2. **Azure Stream Analytics**
   - Create a Stream Analytics job to process and analyze IoT Hub messages in real-time
   - Set up alerts based on message content or patterns

3. **Power BI**
   - Connect to IoT Hub data via Stream Analytics
   - Create real-time dashboards for IoT data visualization

4. **Application Insights**
   - Integrate with your backend services that process IoT Hub data
   - Monitor application performance and availability

## Troubleshooting

### Common Error Messages and Solutions

| Error Message | Possible Causes | Solutions |
|---------------|-----------------|-----------|
| `MQTT connection failed with status code 401` | Invalid credentials | - Verify device ID and key<br>- Check if SAS token has expired<br>- Ensure device is registered in IoT Hub |
| `MQTT connection failed with status code 403` | Authorization failure | - Check if device is disabled in IoT Hub<br>- Verify IP restrictions<br>- Check if IoT Hub has reached message quota |
| `MQTT connection failed with status code 404` | Resource not found | - Verify IoT Hub hostname<br>- Check if device exists in IoT Hub<br>- Verify API version in connection string |
| `MQTT connection failed with status code 500` | Server error | - Check Azure status page for outages<br>- Retry with exponential backoff<br>- Contact Azure support if persistent |
| `MQTT connection timed out` | Network issues | - Check network connectivity<br>- Verify firewall rules (port 8883)<br>- Check DNS resolution |
| `SSL/TLS handshake failed` | TLS configuration issues | - Update CA certificates<br>- Verify TLS version (1.2 required)<br>- Check certificate validity |
| `Message size exceeds limit` | Message too large | - Reduce message size (max 256KB)<br>- Split large messages<br>- Compress message content |
| `Quota exceeded` | Usage limits reached | - Check IoT Hub tier limits<br>- Upgrade to higher tier<br>- Implement throttling in device code |

### Diagnostic Procedures

1. **Connection Diagnostics**

   ```python
   import socket
   import ssl
   import time

   def diagnose_connection(hostname, port=8883):
       print(f"Testing TCP connection to {hostname}:{port}...")
       try:
           # Test basic TCP connection
           start_time = time.time()
           sock = socket.create_connection((hostname, port), timeout=10)
           tcp_time = time.time() - start_time
           print(f"TCP connection successful ({tcp_time:.2f}s)")
           
           # Test TLS handshake
           start_time = time.time()
           context = ssl.create_default_context()
           secure_sock = context.wrap_socket(sock, server_hostname=hostname)
           tls_time = time.time() - start_time
           print(f"TLS handshake successful ({tls_time:.2f}s)")
           
           # Get certificate info
           cert = secure_sock.getpeercert()
           print(f"Server certificate: {cert['subject']}")
           print(f"Certificate expires: {cert['notAfter']}")
           
           secure_sock.close()
           return True
       except socket.timeout:
           print("Connection timed out")
       except socket.gaierror:
           print("DNS resolution failed")
       except ssl.SSLError as e:
           print(f"SSL/TLS error: {e}")
       except Exception as e:
           print(f"Connection error: {e}")
       return False

   # Test connection to IoT Hub
   diagnose_connection("your-iothub.azure-devices.net")
   ```

2. **Device Identity Verification**

   ```bash
   # Check if device exists in IoT Hub
   az iot hub device-identity show \
     --hub-name your-iothub \
     --device-id your-device-id

   # Check device connection state
   az iot hub device-identity show \
     --hub-name your-iothub \
     --device-id your-device-id \
     --query connectionState
   ```

3. **Message Routing Verification**

   ```bash
   # Check message routing endpoints
   az iot hub message-route show \
     --hub-name your-iothub \
     --resource-group your-resource-group \
     --route-name your-route-name

   # Test message routing
   az iot hub message-route test \
     --hub-name your-iothub \
     --resource-group your-resource-group \
     --body '{"temperature": 25}'
   ```

4. **Network Diagnostics**

   ```bash
   # Test network connectivity
   ping your-iothub.azure-devices.net

   # Test port connectivity
   nc -zv your-iothub.azure-devices.net 8883

   # Check TLS handshake
   openssl s_client -connect your-iothub.azure-devices.net:8883 -showcerts
   ```

### Performance Optimization Tips

1. **Connection Optimization**
   - Use persistent connections instead of reconnecting frequently
   - Implement connection pooling for multiple devices
   - Set appropriate keep-alive intervals (60-300 seconds)

2. **Message Optimization**
   - Batch messages when possible
   - Use QoS 1 only for critical messages
   - Compress large payloads
   - Use efficient data formats (JSON, Protocol Buffers, CBOR)

3. **Device Twin Optimization**
   - Minimize the size of reported properties
   - Update reported properties only when they change
   - Use partial updates instead of complete replacements

4. **Retry Strategy Optimization**
   - Implement exponential backoff for retries
   - Set appropriate retry limits
   - Add jitter to retry intervals to prevent thundering herd problems

5. **Resource Utilization**
   - Monitor CPU and memory usage on devices
   - Optimize power consumption for battery-powered devices
   - Implement message throttling based on device capabilities

## Advanced Testing Scenarios

### Load Testing

1. **Device Simulator**

   Create a device simulator to test IoT Hub under load:

   ```python
   import asyncio
   import json
   import time
   import uuid
   from azure.iot.device.aio import IoTHubDeviceClient
   from azure.iot.device import Message

   async def run_device_simulation(device_id, connection_string, message_count, interval):
       # Create client
       client = IoTHubDeviceClient.create_from_connection_string(connection_string)
       
       # Connect to IoT Hub
       await client.connect()
       print(f"Device {device_id} connected")
       
       # Send messages
       for i in range(message_count):
           # Create message
           msg_id = str(uuid.uuid4())
           message = {
               "device_id": device_id,
               "message_id": msg_id,
               "sequence": i + 1,
               "timestamp": time.time(),
               "data": {
                   "temperature": 20 + (i % 10),
                   "humidity": 50 + (i % 20),
                   "pressure": 1000 + (i % 50)
               }
           }
           
           msg = Message(json.dumps(message))
           msg.message_id = msg_id
           msg.content_type = "application/json"
           msg.content_encoding = "utf-8"
           
           # Send message
           await client.send_message(msg)
           print(f"Device {device_id}: Message {i+1}/{message_count} sent")
           
           # Wait for interval
           await asyncio.sleep(interval)
       
       # Disconnect
       await client.disconnect()
       print(f"Device {device_id} disconnected")

   async def main():
       # Simulation parameters
       device_count = 10
       message_count = 100
       interval = 0.5  # seconds
       
       # Connection strings for devices
       connection_strings = [
           "HostName=your-iothub.azure-devices.net;DeviceId=device1;SharedAccessKey=key1",
           "HostName=your-iothub.azure-devices.net;DeviceId=device2;SharedAccessKey=key2",
           # Add more devices as needed
       ]
       
       # Run simulations in parallel
       tasks = []
       for i in range(min(device_count, len(connection_strings))):
           device_id = f"device{i+1}"
           conn_str = connection_strings[i]
           tasks.append(run_device_simulation(device_id, conn_str, message_count, interval))
       
       await asyncio.gather(*tasks)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. **JMeter Testing**

   Use Apache JMeter with the MQTT plugin to perform load testing:
   - Download JMeter and MQTT plugin
   - Create a test plan with multiple threads (devices)
   - Configure MQTT samplers with IoT Hub connection details
   - Run tests with increasing load to find performance limits

### Security Testing

1. **Certificate Validation**

   Test certificate validation by attempting to connect with invalid certificates:

   ```python
   import ssl
   import paho.mqtt.client as mqtt

   def test_invalid_certificate():
       client = mqtt.Client(client_id="test-device")
       client.username_pw_set("your-iothub.azure-devices.net/test-device/?api-version=2021-04-12", "invalid-sas-token")
       
       # Configure TLS with self-signed certificate
       client.tls_set(
           ca_certs=None,
           certfile="invalid-cert.pem",
           keyfile="invalid-key.pem",
           cert_reqs=ssl.CERT_REQUIRED,
           tls_version=ssl.PROTOCOL_TLSv1_2
       )
       
       # Connect to IoT Hub (should fail)
       try:
           client.connect("your-iothub.azure-devices.net", 8883, 60)
           print("Connection succeeded (unexpected)")
           return False
       except Exception as e:
           print(f"Connection failed as expected: {e}")
           return True
   ```

2. **Token Expiry Testing**

   Test behavior when SAS tokens expire:

   ```python
   import time
   from azure.iot.device import IoTHubDeviceClient, Message

   def test_token_expiry():
       # Create a SAS token with very short expiry (10 seconds)
       short_lived_token = generate_sas_token("your-iothub.azure-devices.net/devices/test-device", "device-key", expiry=10)
       
       # Create connection string with short-lived token
       conn_str = f"HostName=your-iothub.azure-devices.net;DeviceId=test-device;SharedAccessSignature={short_lived_token}"
       
       # Create client
       client = IoTHubDeviceClient.create_from_connection_string(conn_str)
       
       # Connect to IoT Hub
       client.connect()
       print("Connected successfully")
       
       # Send a message
       msg = Message("Test message")
       client.send_message(msg)
       print("First message sent successfully")
       
       # Wait for token to expire
       print("Waiting for token to expire...")
       time.sleep(15)
       
       # Try to send another message (should fail)
       try:
           client.send_message(Message("Second test message"))
           print("Second message sent (unexpected)")
           return False
       except Exception as e:
           print(f"Second message failed as expected: {e}")
           return True
   ```

By following these testing and validation procedures, you can ensure reliable connectivity between your devices and Azure IoT Hub using the MQTT protocol, effectively monitor message flow, and quickly troubleshoot any issues that arise.
