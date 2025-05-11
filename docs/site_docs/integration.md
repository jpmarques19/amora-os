# AmoraSDK Integration with AmoraOS

## Integration Overview

The AmoraSDK integrates with the existing AmoraOS system by running alongside the main player application and providing a network interface for client applications to control the player and receive status updates.

## Integration Diagram

```
+----------------------------------------------+
|                  DEVICE                      |
|                                              |
|  +------------------+  +------------------+  |
|  |                  |  |                  |  |
|  |   AmoraOS Main   |  |   AmoraSDK       |  |
|  |   Application    |  |   Server         |  |
|  |                  |  |                  |  |
|  +--------+---------+  +--------+---------+  |
|           |                     |            |
|           v                     v            |
|  +------------------+  +------------------+  |
|  |                  |  |                  |  |
|  |   MPD            |  |   FastAPI        |  |
|  |   (Music Player  |  |   (HTTP +        |  |
|  |    Daemon)       |  |    WebSocket)    |  |
|  |                  |  |                  |  |
|  +--------+---------+  +--------+---------+  |
|           |                     |            |
+-----------|---------------------|------------+
            |                     |
            v                     v
    +----------------+    +----------------+
    |                |    |                |
    |  Audio Output  |    |  Network       |
    |                |    |  Interface     |
    +----------------+    +----------------+
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

## Integration Components

### AmoraOS Main Application

The existing AmoraOS main application continues to function as before, controlling the MPD for audio playback. It remains the primary controller for the player device.

### AmoraSDK Server

The AmoraSDK Server runs alongside the main application and provides:

1. A network interface for client applications
2. Real-time status updates via WebSocket
3. Control commands via HTTP API

### MPD (Music Player Daemon)

MPD remains the core audio playback engine, controlled by both:

1. The AmoraOS main application
2. The AmoraSDK Server (through the PlayerInterface)

### FastAPI Server

The FastAPI server exposes:

1. HTTP endpoints for player control
2. WebSocket endpoint for real-time status updates

## Integration Methods

There are two main approaches to integrate the AmoraSDK with the existing AmoraOS system:

### 1. Standalone Process

In this approach, the AmoraSDK Server runs as a separate process from the main application:

- **Pros**:
  - Minimal changes to existing code
  - Independent lifecycle (can be started/stopped separately)
  - Failure isolation

- **Cons**:
  - Potential synchronization issues
  - Duplicate connections to MPD
  - Higher resource usage

### 2. Integrated Component

In this approach, the AmoraSDK Server is integrated into the main application:

- **Pros**:
  - Single connection to MPD
  - Shared state and synchronization
  - Lower resource usage

- **Cons**:
  - More changes to existing code
  - Shared lifecycle (starts/stops with main application)
  - Potential for bugs affecting both components

## Recommended Approach

The recommended approach is to start with the **Standalone Process** for initial development and testing, then move to the **Integrated Component** approach for production deployment.

This allows for:

1. Rapid development and testing of the SDK
2. Minimal disruption to the existing system
3. Gradual integration into the main application
