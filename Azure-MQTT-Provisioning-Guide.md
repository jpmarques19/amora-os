# Azure MQTT Provisioning Guide

This document provides step-by-step instructions for provisioning Azure IoT Hub for MQTT broker functionality, including CLI commands, portal instructions, resource recommendations, SDK configuration, and production deployment best practices.

## Provisioning Azure IoT Hub

### Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed and configured
- Understanding of your IoT solution requirements (device count, message volume, etc.)

### Resource Recommendations

| Resource | Recommendation | Notes |
|----------|---------------|-------|
| **Resource Group** | Create a dedicated resource group | Facilitates management and billing tracking |
| **Region** | Select based on proximity to devices | Consider using paired regions for disaster recovery |
| **SKU** | Standard tier (S1) | Provides all features needed for production |
| **Capacity Units** | Start with 1-2 units | Each S1 unit supports 400,000 messages/day |
| **Partition Count** | 4 (default) | Increase for high-throughput scenarios |
| **Retention Time** | 1-7 days | Based on your data processing requirements |

### Using Azure Portal

1. **Create IoT Hub**
   - Sign in to the [Azure Portal](https://portal.azure.com)
   - Click "Create a resource" and search for "IoT Hub"
   - Click "Create"

2. **Basic Configuration**
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or select existing
   - **IoT Hub Name**: Enter a globally unique name (e.g., `company-iot-prod`)
   - **Region**: Select appropriate region
   - Click "Next: Networking"

3. **Networking Configuration**
   - **Connectivity**: Select "Public endpoint (all networks)" for standard setup or "Public endpoint (selected networks)" for enhanced security
   - **Private Endpoint**: Configure if needed for enhanced security
   - Click "Next: Management"

4. **Management Configuration**
   - **Pricing and scale tier**: Select "Standard (S1)"
   - **Number of IoT Hub units**: Start with 1-2 based on expected load
   - **Device-to-cloud partitions**: Leave at default (4) or increase for high throughput
   - Click "Next: Tags"

5. **Tags Configuration**
   - Add appropriate tags for resource management (e.g., Environment=Production, Project=IoT)
   - Click "Next: Review + create"

6. **Review and Create**
   - Review all settings
   - Click "Create"

### Using Azure CLI

The following commands provision an Azure IoT Hub with recommended settings:

```bash
# Login to Azure (if not already logged in)
az login

# Set variables
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="iot-production-rg"
LOCATION="eastus"
IOT_HUB_NAME="company-iot-prod"
SKU="S1"
CAPACITY=1

# Set the subscription context
az account set --subscription $SUBSCRIPTION_ID

# Create resource group if it doesn't exist
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create IoT Hub
az iot hub create \
  --name $IOT_HUB_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku $SKU \
  --unit $CAPACITY \
  --partition-count 4 \
  --retention-time 1

# Get the connection string for the IoT Hub
az iot hub connection-string show --hub-name $IOT_HUB_NAME --resource-group $RESOURCE_GROUP
```

### Using Azure Resource Manager (ARM) Template

For automated deployments, you can use an ARM template. Here's a sample template for IoT Hub:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "iotHubName": {
      "type": "string",
      "defaultValue": "company-iot-prod",
      "metadata": {
        "description": "Name of the IoT Hub"
      }
    },
    "location": {
      "type": "string",
      "defaultValue": "eastus",
      "metadata": {
        "description": "Location for the IoT Hub"
      }
    },
    "skuName": {
      "type": "string",
      "defaultValue": "S1",
      "metadata": {
        "description": "SKU Name for IoT Hub"
      }
    },
    "capacity": {
      "type": "int",
      "defaultValue": 1,
      "metadata": {
        "description": "Number of IoT Hub units"
      }
    }
  },
  "resources": [
    {
      "type": "Microsoft.Devices/IotHubs",
      "apiVersion": "2021-07-02",
      "name": "[parameters('iotHubName')]",
      "location": "[parameters('location')]",
      "sku": {
        "name": "[parameters('skuName')]",
        "capacity": "[parameters('capacity')]"
      },
      "properties": {
        "eventHubEndpoints": {
          "events": {
            "retentionTimeInDays": 1,
            "partitionCount": 4
          }
        },
        "cloudToDevice": {
          "defaultTtlAsIso8601": "PT1H",
          "maxDeliveryCount": 10,
          "feedback": {
            "lockDurationAsIso8601": "PT5S",
            "ttlAsIso8601": "PT1H",
            "maxDeliveryCount": 10
          }
        },
        "enableFileUploadNotifications": false,
        "messagingEndpoints": {
          "fileNotifications": {
            "lockDurationAsIso8601": "PT1M",
            "ttlAsIso8601": "PT1H",
            "maxDeliveryCount": 10
          }
        }
      }
    }
  ],
  "outputs": {
    "iotHubConnectionString": {
      "type": "string",
      "value": "[concat('HostName=', reference(resourceId('Microsoft.Devices/IotHubs', parameters('iotHubName'))).hostName, ';SharedAccessKeyName=iothubowner;SharedAccessKey=', listKeys(resourceId('Microsoft.Devices/IotHubs', parameters('iotHubName')), '2021-07-02').value[0].primaryKey)]"
    }
  }
}
```

To deploy this template:

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file iot-hub-template.json \
  --parameters iotHubName=$IOT_HUB_NAME location=$LOCATION
```

## Registering Devices

### Using Azure Portal

1. Navigate to your IoT Hub in the Azure Portal
2. Select "Devices" from the left menu
3. Click "New" to add a new device
4. Enter a Device ID
5. Select authentication type (Symmetric key or X.509 certificate)
6. Click "Save"

### Using Azure CLI

```bash
# Register a new device with symmetric key authentication
az iot hub device-identity create \
  --hub-name $IOT_HUB_NAME \
  --device-id "device001" \
  --auth-method "shared_private_key"

# Get the device connection string
az iot hub device-identity connection-string show \
  --hub-name $IOT_HUB_NAME \
  --device-id "device001"

# Register a device with X.509 certificate authentication
az iot hub device-identity create \
  --hub-name $IOT_HUB_NAME \
  --device-id "device002" \
  --auth-method "x509_ca" \
  --primary-thumbprint "0000000000000000000000000000000000000000"
```

### Using Device Provisioning Service (DPS)

For large-scale device provisioning, use Azure IoT Hub Device Provisioning Service:

1. **Create DPS Instance**

```bash
# Create DPS instance
az iot dps create \
  --name "company-iot-dps" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Link DPS to IoT Hub
az iot dps linked-hub create \
  --dps-name "company-iot-dps" \
  --resource-group $RESOURCE_GROUP \
  --connection-string $(az iot hub connection-string show --hub-name $IOT_HUB_NAME --resource-group $RESOURCE_GROUP --query connectionString -o tsv) \
  --location $LOCATION
```

2. **Create Enrollment Group (for X.509 certificates)**

```bash
# Create enrollment group using root CA certificate
az iot dps enrollment-group create \
  --dps-name "company-iot-dps" \
  --resource-group $RESOURCE_GROUP \
  --enrollment-id "production-devices" \
  --certificate-path "/path/to/root-ca.pem" \
  --provisioning-status "enabled" \
  --initial-twin-properties "{\"tags\":{\"environment\":\"production\"}}"
```

## SDK Configuration for Azure IoT Hub

### Python SDK Example

```python
import os
import time
import json
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

# Connection string format: "HostName=<iothub_host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
CONNECTION_STRING = "HostName=company-iot-prod.azure-devices.net;DeviceId=device001;SharedAccessKey=your_device_key"

def create_client():
    # Create IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    
    # Define method handlers
    def method_request_handler(method_request):
        print(f"Received method request: {method_request.name}")
        payload = {"result": True, "data": "Method executed successfully"}
        status = 200
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        client.send_method_response(method_response)
        
    # Set method request handler
    client.on_method_request_received = method_request_handler
    
    # Connect to IoT Hub
    client.connect()
    return client

def send_telemetry(client):
    # Create message
    msg = Message(json.dumps({
        "temperature": 25.0,
        "humidity": 60.0,
        "timestamp": time.time()
    }))
    
    # Add custom properties
    msg.custom_properties["type"] = "telemetry"
    msg.content_type = "application/json"
    msg.content_encoding = "utf-8"
    
    # Send message
    client.send_message(msg)
    print("Message sent")

def main():
    try:
        # Create client
        client = create_client()
        
        # Send telemetry
        while True:
            send_telemetry(client)
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("IoT Hub client stopped")
        client.disconnect()

if __name__ == "__main__":
    main()
```

### Node.js SDK Example

```javascript
const { Mqtt } = require('azure-iot-device-mqtt');
const { DeviceClient, Message } = require('azure-iot-device');

// Connection string format: "HostName=<iothub_host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
const connectionString = "HostName=company-iot-prod.azure-devices.net;DeviceId=device001;SharedAccessKey=your_device_key";

// Create IoT Hub client
const client = DeviceClient.fromConnectionString(connectionString, Mqtt);

// Connect to IoT Hub
client.open((err) => {
  if (err) {
    console.error('Error connecting to IoT Hub:', err);
    return;
  }
  
  console.log('Connected to IoT Hub');
  
  // Set up direct method handler
  client.onDeviceMethod('executeCommand', (request, response) => {
    console.log(`Received method request: ${request.methodName}`);
    
    // Process the command
    const payload = {
      result: true,
      data: 'Command executed successfully'
    };
    
    // Send response
    response.send(200, payload, (err) => {
      if (err) {
        console.error('Error sending method response:', err);
      }
    });
  });
  
  // Send telemetry data
  const sendTelemetry = () => {
    const data = {
      temperature: 25.0,
      humidity: 60.0,
      timestamp: Date.now()
    };
    
    const message = new Message(JSON.stringify(data));
    message.properties.add('type', 'telemetry');
    message.contentType = 'application/json';
    message.contentEncoding = 'utf-8';
    
    client.sendEvent(message, (err) => {
      if (err) {
        console.error('Error sending message:', err);
      } else {
        console.log('Message sent');
      }
      
      // Schedule next telemetry
      setTimeout(sendTelemetry, 5000);
    });
  };
  
  // Start sending telemetry
  sendTelemetry();
});
```

## Production Deployment Best Practices

### High Availability Configuration

1. **Use Paired Regions**
   - Deploy IoT Hub in paired Azure regions for disaster recovery
   - Use Traffic Manager for automatic failover

2. **Implement Message Persistence**
   - Configure message persistence in your devices to handle temporary connectivity issues
   - Implement local storage and message queuing on devices

3. **Use Device Twins for Configuration**
   - Store device configuration in device twins for resilience
   - Implement configuration synchronization on device reconnection

4. **Implement Retry Logic**
   - Use exponential backoff for connection retries
   - Implement circuit breaker patterns for handling persistent failures

### Monitoring and Alerting Setup

1. **Enable Diagnostics Settings**
   ```bash
   az monitor diagnostic-settings create \
     --name "iot-hub-diagnostics" \
     --resource $IOT_HUB_NAME \
     --resource-group $RESOURCE_GROUP \
     --resource-type "Microsoft.Devices/IotHubs" \
     --logs '[{"category": "Connections", "enabled": true}, {"category": "DeviceTelemetry", "enabled": true}]' \
     --metrics '[{"category": "AllMetrics", "enabled": true}]' \
     --workspace $(az monitor log-analytics workspace show --workspace-name "iot-analytics" --resource-group $RESOURCE_GROUP --query id -o tsv)
   ```

2. **Create Alert Rules**
   ```bash
   # Create alert for high device connection failures
   az monitor metrics alert create \
     --name "HighConnectionFailures" \
     --resource-group $RESOURCE_GROUP \
     --scopes $(az iot hub show --name $IOT_HUB_NAME --resource-group $RESOURCE_GROUP --query id -o tsv) \
     --condition "avg d2c.telemetry.ingress.failures.count > 100" \
     --window-size 5m \
     --evaluation-frequency 1m \
     --action $(az monitor action-group show --name "iot-ops-team" --resource-group $RESOURCE_GROUP --query id -o tsv)
   ```

3. **Set Up Azure Monitor Workbooks**
   - Create custom workbooks for IoT Hub monitoring
   - Include device connectivity, message throughput, and error metrics

4. **Implement Log Analytics Queries**
   - Set up queries for common issues
   - Create dashboards for operational visibility

### Cost Optimization Strategies

1. **Right-size IoT Hub Units**
   - Start with minimal units and scale based on actual usage
   - Monitor daily message count to optimize tier selection

2. **Implement Message Batching**
   - Batch multiple readings into single messages where appropriate
   - Reduce per-message costs and network overhead

3. **Use Message Routing Efficiently**
   - Configure message routing to minimize duplicate processing
   - Use message enrichment to add metadata at the hub instead of on devices

4. **Optimize Message Size**
   - Compress payloads for large messages
   - Use efficient data formats (e.g., Protocol Buffers, CBOR)

5. **Implement Message Filtering at Source**
   - Filter non-essential data at the device level
   - Use device twins for configuration of filtering parameters

## Scaling Considerations

1. **Partition Planning**
   - Each IoT Hub has a default of 4 partitions
   - Plan partition count based on expected throughput (cannot be changed after creation)

2. **Device Registration Scaling**
   - Use bulk device registration for large deployments
   - Implement device provisioning service for automatic scaling

3. **Message Throughput Scaling**
   - Monitor message throughput metrics
   - Scale IoT Hub units when approaching 50-70% of capacity

4. **Regional Distribution**
   - For global deployments, consider multiple regional IoT Hubs
   - Implement a strategy for cross-region message routing

By following these provisioning guidelines and best practices, you can establish a robust, scalable, and cost-effective Azure IoT Hub environment for your MQTT broker needs in production.
