# AmoraSDK Azure IoT Architecture

## Overview

This architecture leverages Azure IoT Hub and Event Hub to provide device control and real-time status synchronization between AmoraOS devices and client applications.

## Architecture Diagram

```
+----------------------------------+      +----------------------------------+
|          DEVICE SIDE             |      |           CLOUD                  |
|                                  |      |                                  |
|  +----------------------------+  |      |  +----------------------------+  |
|  |                            |  |      |  |                            |  |
|  |      AmoraOS Player        |  |      |  |      Azure IoT Hub         |  |
|  |     (MusicPlayer class)    |  |      |  |                            |  |
|  |                            |  |      |  |                            |  |
|  +------------+---------------+  |      |  +------------+---------------+  |
|               |                  |      |               |                  |
|               | Interface        |      |               |                  |
|               v                  |      |               v                  |
|  +----------------------------+  |      |  +----------------------------+  |
|  |                            |  |      |  |                            |  |
|  |     IoT Device Client      +<-+------+->+     Device Twin            |  |
|  |  (Azure IoT SDK)           |  |      |  |     (Device State)         |  |
|  |                            |  |      |  |                            |  |
|  +----------------------------+  |      |  +----------------------------+  |
|               |                  |      |               |                  |
|               |                  |      |               v                  |
|               |                  |      |  +----------------------------+  |
|               |                  |      |  |                            |  |
|               |                  |      |  |      Azure Event Hub       |  |
|               |                  |      |  |  (Real-time Status)        |  |
|               |                  |      |  |                            |  |
|               |                  |      |  +------------+---------------+  |
|               |                  |      |               |                  |
+---------------+------------------+      +---------------+------------------+
                |                                         |
                |                                         |
                v                                         v
       +------------------+                     +------------------+
       |                  |                     |                  |
       |  Direct Methods  |                     |  Event Hub SDK   |
       |  (Commands)      |                     |  (Status Updates)|
       |                  |                     |                  |
       +--------+---------+                     +--------+---------+
                |                                         |
                |                                         |
                v                                         v
       +--------------------------------------------------+
       |                                                  |
       |               CLIENT APPLICATIONS                |
       |          (Web, Mobile, Desktop Apps)             |
       |                                                  |
       +--------------------------------------------------+
```

## Component Details

### Device Side

1. **AmoraOS Player (MusicPlayer class)**
   - Core player functionality
   - Controls MPD for audio playback
   - Manages playlists and tracks

2. **IoT Device Client (Azure IoT SDK)**
   - Connects to Azure IoT Hub
   - Receives direct method calls for commands
   - Updates device twin with current state
   - Sends telemetry for real-time status updates

### Cloud Services

1. **Azure IoT Hub**
   - Manages device identity and security
   - Routes commands to devices via direct methods
   - Maintains device state via device twins
   - Routes telemetry to Event Hub

2. **Device Twin**
   - Digital representation of device state
   - Stores current player status
   - Enables desired state synchronization
   - Provides persistent state storage

3. **Azure Event Hub**
   - Handles high-volume telemetry data
   - Enables real-time status streaming
   - Supports multiple consumers
   - Provides message replay capabilities

### Client Side

1. **Azure IoT SDK (Direct Methods)**
   - Sends commands to devices via IoT Hub
   - Reads and updates device twins
   - Handles command acknowledgments

2. **Event Hub SDK**
   - Receives real-time status updates
   - Processes telemetry data
   - Enables real-time UI updates

3. **Client Applications**
   - Web, mobile, or desktop applications
   - Provide user interface for player control
   - Display real-time player status

## Communication Flows

### Command Flow (Client to Device)

1. Client application calls Azure IoT Hub SDK to invoke a direct method on the device
2. Azure IoT Hub routes the direct method call to the device
3. IoT Device Client receives the method call and executes the corresponding player command
4. Device returns the command result to IoT Hub
5. IoT Hub returns the result to the client application

### Status Update Flow (Device to Client)

1. Device periodically collects player status
2. IoT Device Client sends status as telemetry to IoT Hub
3. IoT Hub routes telemetry to Event Hub
4. Client applications receive status updates from Event Hub
5. UI is updated with the latest player status

### Device State Synchronization

1. Device updates its reported properties in the device twin
2. Client applications can read the device twin to get the current state
3. Client applications can update desired properties to request state changes
4. Device receives desired property changes and applies them

## Device Twin Structure

The device twin maintains the current state of the player:

```json
{
  "properties": {
    "reported": {
      "status": {
        "state": "play",
        "volume": 80,
        "current_song": {
          "title": "Song Title",
          "artist": "Artist Name",
          "album": "Album Name",
          "file": "song.mp3",
          "duration": 180,
          "position": 45
        },
        "playlist": "My Playlist"
      },
      "playlists": ["Playlist 1", "Playlist 2"],
      "lastUpdated": "2023-06-15T12:34:56Z"
    },
    "desired": {
      "command": {
        "action": "play",
        "parameters": {}
      }
    }
  }
}
```

## Direct Methods

The following direct methods are implemented for player control:

- `play`: Start or resume playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Skip to next track
- `previous`: Skip to previous track
- `setVolume`: Set volume level
- `getPlaylists`: Get available playlists

## Telemetry Schema

Real-time status updates are sent as telemetry with this schema:

```json
{
  "messageType": "playerStatus",
  "deviceId": "amora-player-001",
  "timestamp": "2023-06-15T12:34:56Z",
  "status": {
    "state": "play",
    "volume": 80,
    "current_song": {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "file": "song.mp3",
      "duration": 180,
      "position": 45
    },
    "playlist": "My Playlist"
  }
}
```
