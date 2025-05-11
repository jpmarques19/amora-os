# AmoraOS Real-time Communication

## Overview

AmoraOS devices need to communicate their state changes (play, pause, etc.) to client applications in real-time with minimal latency. This architecture uses a dedicated MQTT broker to provide low-latency, push-based communication between devices and client applications.

## Key Features

- **Real-time State Updates**: Device state changes are pushed to client applications in real-time
- **Low Latency**: End-to-end latency of 30-100ms for state updates
- **Secure Communication**: TLS encryption, client certificates, and JWT authentication
- **Reliable Delivery**: QoS guarantees for message delivery
- **Scalable Architecture**: Supports 1,400+ devices and 5,000+ concurrent client connections

## Architecture Components

![Architecture Diagram](images/realtime_architecture.png)

### Components

1. **AmoraOS Devices**
   - 1,400+ music player devices
   - Run MPD for music playback
   - Connect to both IoT Hub and MQTT broker

2. **Azure IoT Hub**
   - Device provisioning and identity management
   - Configuration and settings management
   - Firmware/software updates
   - Non-real-time telemetry (usage statistics, diagnostics)
   - Long-term data storage and analytics

3. **MQTT Broker**
   - Dedicated broker for real-time communication
   - Hosted in Azure
   - Handles device state updates and commands
   - Provides push-based communication to clients

4. **Client Applications**
   - Web, mobile, and desktop applications
   - Connect to MQTT broker for real-time updates
   - Connect to backend services for non-real-time operations

5. **Backend Services**
   - User authentication and authorization
   - Device management
   - Analytics and reporting
   - Integration with other systems

## Communication Flows

### Device State Updates

1. Device detects state change (play, pause, etc.)
2. Device publishes state update to MQTT broker
3. MQTT broker pushes update to subscribed clients
4. Clients update UI in real-time

### Device Commands

1. Client sends command to device via MQTT broker
2. MQTT broker routes command to device
3. Device executes command and publishes state update
4. MQTT broker pushes state update to subscribed clients

## MQTT Topic Structure

```
amora/devices/{device_id}/state           # Current device state
amora/devices/{device_id}/commands        # Commands to the device
amora/devices/{device_id}/responses       # Command responses
amora/devices/{device_id}/connection      # Connection status
```

## Security Model

1. **Authentication**
   - Devices: Client certificates
   - Users: JWT tokens via Azure AD B2C

2. **Authorization**
   - Topic-based access control
   - User-to-device mapping in backend

3. **Transport Security**
   - TLS 1.2+ for all connections
   - Certificate validation

4. **Message Security**
   - Message signing for integrity
   - Payload encryption for sensitive data

## Performance Characteristics

- **Latency**: 30-100ms end-to-end
- **Throughput**: 1000+ messages per second
- **Reliability**: QoS 1 for state updates, QoS 2 for critical commands
- **Scalability**: Supports 10,000+ concurrent connections

## Integration with Existing Systems

- **IoT Hub Integration**: Devices maintain connections to both IoT Hub and MQTT broker
- **Backend Integration**: Backend services can publish/subscribe to MQTT topics
- **Monitoring Integration**: Metrics and logs integrated with Azure Monitor

## Failure Modes and Recovery

1. **MQTT Broker Failure**
   - Automatic failover to standby broker
   - Devices and clients reconnect automatically
   - Last Will and Testament (LWT) for device status

2. **Device Connection Loss**
   - LWT message published to notify clients
   - Automatic reconnection with exponential backoff
   - State synchronization on reconnection

3. **Client Connection Loss**
   - Automatic reconnection with exponential backoff
   - State synchronization on reconnection
   - Offline message queueing

## Deployment Model

- **MQTT Broker**: Deployed in Azure Container Apps or AKS
- **High Availability**: Multi-zone deployment with load balancing
- **Scaling**: Horizontal scaling based on connection count and message throughput
- **Monitoring**: Azure Monitor integration for metrics and alerts

## Implementation Steps

The implementation is divided into the following phases:

1. **Infrastructure Setup**: Deploy MQTT broker in Azure
2. **SDK Development**: Develop the Amora Sync SDK
3. **Device Implementation**: Update device firmware to support MQTT
4. **Client Application Integration**: Integrate SDK with client applications
5. **Testing and Optimization**: Test and optimize performance
6. **Deployment and Rollout**: Roll out to all devices

## Getting Started

### Prerequisites

- Azure subscription
- Azure CLI
- Docker
- Node.js 14+
- Python 3.8+

### Setup

1. Deploy the MQTT broker using the provided templates
2. Implement the Amora Sync SDK
3. Update device firmware
4. Integrate with client applications
