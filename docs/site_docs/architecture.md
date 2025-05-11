# AmoraSDK Architecture

## Overview

The AmoraSDK provides a client-server architecture for controlling the AmoraOS player device and receiving real-time status updates. The architecture consists of three main components:

1. **Device Side (Server)**: Python SDK that runs on the player device
2. **Client SDK**: JavaScript/TypeScript library for client applications
3. **Client Applications**: Web or mobile applications that use the Client SDK

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
|  |     AmoraSDK Server        |  |      |  |      AmoraSDK Client       |  |
|  |  (PlayerInterface class)   |  |      |  |     (AmoraClient class)    |  |
|  |                            |  |      |  |                            |  |
|  +----------------------------+  |      |  +----------------------------+  |
|               |                  |      |               |                  |
|               | Exposes          |      |               | Connects to      |
|               v                  |      |               |                  |
|  +----------------------------+  |      |               |                  |
|  |                            |  |      |               |                  |
|  |      FastAPI Server        +<-+------+---------------+                  |
|  |  (HTTP API + WebSocket)    |  |      |                                  |
|  |                            |  |      |                                  |
|  +----------------------------+  |      |                                  |
|                                  |      |                                  |
+----------------------------------+      +----------------------------------+

                HTTP/WebSocket Communication
```

## Component Details

### Device Side (Server)

1. **AmoraOS Player (MusicPlayer class)**
   - Core player functionality
   - Controls MPD for audio playback
   - Manages playlists and tracks

2. **PlayerInterface**
   - Wrapper around MusicPlayer
   - Provides a clean interface for the SDK server
   - Handles error handling and logging

3. **AmoraServer**
   - FastAPI server that exposes:
     - HTTP endpoints for player control
     - WebSocket endpoint for real-time status updates
   - Manages client connections
   - Periodically sends status updates to connected clients

### Client SDK

1. **AmoraApiClient**
   - HTTP client for the API endpoints
   - Methods for controlling the player (play, pause, etc.)
   - Error handling and retries

2. **AmoraWebSocketClient**
   - WebSocket client for real-time status updates
   - Event-based architecture for status updates
   - Automatic reconnection

3. **AmoraClient**
   - High-level client that combines API and WebSocket clients
   - Simple interface for applications
   - Handles connection management

### Client Applications

1. **React Test App**
   - Simple player UI
   - Real-time status display
   - Playlist management

## Communication Flow

### Control Flow (Client to Device)

1. User interacts with the client application (e.g., clicks play button)
2. Client application calls AmoraClient method (e.g., `client.play()`)
3. AmoraClient uses AmoraApiClient to send HTTP request to server
4. Server receives request and calls PlayerInterface method
5. PlayerInterface calls MusicPlayer method
6. MusicPlayer controls MPD to perform the action

### Status Update Flow (Device to Client)

1. AmoraServer periodically polls MusicPlayer for status
2. AmoraServer sends status updates to all connected WebSocket clients
3. AmoraWebSocketClient receives status update
4. AmoraWebSocketClient notifies registered callbacks
5. Client application updates UI based on new status

## API Endpoints

### HTTP API

- `GET /api/status` - Get player status
- `GET /api/playlists` - Get available playlists
- `POST /api/play` - Start or resume playback
- `POST /api/pause` - Pause playback
- `POST /api/stop` - Stop playback
- `POST /api/next` - Skip to next track
- `POST /api/previous` - Skip to previous track
- `POST /api/volume` - Set volume level

### WebSocket API

- `WebSocket /ws` - Real-time status updates
