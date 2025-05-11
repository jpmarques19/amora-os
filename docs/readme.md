# AmoraOS Documentation

This directory contains comprehensive documentation for the AmoraOS project, including the edge device implementation and the AmoraSDK.

## SDK Documentation

- [Architecture](site_docs/architecture.md) - Overview of the AmoraSDK architecture
- [Azure Architecture](site_docs/azure_architecture.md) - Azure IoT Hub integration architecture
- [Azure Implementation](site_docs/azure_implementation.md) - Azure IoT Hub implementation details
- [Client Development](site_docs/client_development.md) - Guide for developing client applications
- [Data Flow](site_docs/data_flow.md) - Data flow between components
- [Device Changes](site_docs/device_changes.md) - Changes required for device integration
- [Integration](site_docs/integration.md) - Integration with AmoraOS

## Project Documentation

- [Azure Resources](site_docs/azure_resources.md) - Azure resources used in the project
- [Implementation Plan](site_docs/implementation_plan.md) - Implementation plan for the project
- [Realtime Architecture](site_docs/realtime_architecture.md) - Real-time communication architecture
- [Realtime README](site_docs/realtime_readme.md) - Real-time communication overview

## User Documentation

- [Getting Started](site_docs/getting_started.md) - Getting started guide
- [Configuration](site_docs/configuration.md) - Configuration options
- [Developer Guide](site_docs/developer_guide.md) - Developer guide
- [IoT Integration](site_docs/iot_integration.md) - IoT integration details

## Quick Start

For a quick overview of the AmoraOS project, see the main README file in the root directory.

## Architecture Diagram

```
+----------------------------------+      +----------------------------------+
|          DEVICE SIDE             |      |           CLIENT SIDE            |
|                                  |      |                                  |
|  +----------------------------+  |      |  +----------------------------+  |
|  |                            |  |      |  |                            |  |
|  |      AmoraOS Player        |  |      |  |     Client Application     |  |
|  |     (MusicPlayer class)    |  |      |  |      (React, Angular)      |  |
|  |                            |  |      |  |                            |  |
|  +------------+---------------+  |      |  +------------+---------------+  |
|               |                  |      |               |                  |
|               | Interface        |      |               | Uses             |
|               v                  |      |               v                  |
|  +----------------------------+  |      |  +----------------------------+  |
|  |                            |  |      |  |                            |  |
|  |     AmoraSDK Device        |  |      |  |      AmoraSDK Client       |  |
|  |  (Device Module)           |  |      |  |     (Client Module)        |  |
|  |                            |  |      |  |                            |  |
|  +----------------------------+  |      |  +----------------------------+  |
|               |                  |      |               |                  |
|               | Connects to      |      |               | Connects to      |
|               v                  |      |               v                  |
|  +----------------------------+  |      |  +----------------------------+  |
|  |                            |  |      |  |                            |  |
|  |      MQTT Broker           +<-+------+->+      MQTT Broker           |  |
|  |  (Mosquitto, HiveMQ)       |  |      |  |  (Mosquitto, HiveMQ)       |  |
|  |                            |  |      |  |                            |  |
|  +----------------------------+  |      |  +----------------------------+  |
|               |                  |      |                                  |
|               | Connects to      |      |                                  |
|               v                  |      |                                  |
|  +----------------------------+  |      |                                  |
|  |                            |  |      |                                  |
|  |      Azure IoT Hub         |  |      |                                  |
|  |  (Device Management)       |  |      |                                  |
|  |                            |  |      |                                  |
|  +----------------------------+  |      |                                  |
|                                  |      |                                  |
+----------------------------------+      +----------------------------------+

                MQTT Communication + Azure IoT Hub Integration
```

## Integration Diagram

```
+----------------------------------------------+
|                  DEVICE                      |
|                                              |
|  +------------------+  +------------------+  |
|  |                  |  |                  |  |
|  |   AmoraOS Main   |  |   AmoraSDK       |  |
|  |   Application    |  |   Device Client   |  |
|  |                  |  |                  |  |
|  +--------+---------+  +--------+---------+  |
|           |                     |            |
|           v                     v            |
|  +------------------+  +------------------+  |
|  |                  |  |                  |  |
|  |   MPD            |  |   MQTT Client    |  |
|  |   (Music Player  |  |   (Paho MQTT)    |  |
|  |    Daemon)       |  |                  |  |
|  |                  |  |                  |  |
|  +--------+---------+  +--------+---------+  |
|           |                     |            |
+-----------|---------------------|------------+
            |                     |
            v                     v
    +----------------+    +----------------+
    |                |    |                |
    |  Audio Output  |    |  MQTT Broker   |
    |                |    |                |
    +----------------+    +--------+-------+
                                  |
                                  |
                                  v
                     +------------------+
                     |                  |
                     |  Client          |
                     |  Applications    |
                     |                  |
                     +------------------+
```

## Data Flow Diagram

```
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
|  Client          |    |  MQTT            |    |  AmoraOS         |
|  Application     |    |  Broker          |    |  Player          |
|                  |    |                  |    |                  |
+--------+---------+    +--------+---------+    +--------+---------+
         |                      |                       |
         |                      |                       |
         |  1. Command Message  |                       |
         +--------------------->|                       |
         |                      |  2. Command Message   |
         |                      +---------------------->|
         |                      |                       |
         |                      |  3. Response Message  |
         |                      |<----------------------+
         |  4. Response Message |                       |
         |<---------------------+                       |
         |                      |                       |
         |                      |  5. Status Update     |
         |                      |<----------------------+
         |  6. Status Update    |                       |
         |<---------------------+                       |
         |                      |                       |
```
