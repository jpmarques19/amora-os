# AmoraSDK Data Flow

## Overview

This document explains the data flow and communication between the different components of the AmoraSDK system.

## Data Flow Diagram

```
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
|  Client          |    |  AmoraSDK        |    |  AmoraOS         |
|  Application     |    |  Server          |    |  Player          |
|                  |    |                  |    |                  |
+--------+---------+    +--------+---------+    +--------+---------+
         |                      |                       |
         |                      |                       |
         |  1. Command Request  |                       |
         +--------------------->|                       |
         |                      |  2. Player Command    |
         |                      +---------------------->|
         |                      |                       |
         |                      |  3. Command Result    |
         |                      |<----------------------+
         |  4. Command Response |                       |
         |<---------------------+                       |
         |                      |                       |
         |                      |  5. Status Poll       |
         |                      +---------------------->|
         |                      |                       |
         |                      |  6. Status Data       |
         |                      |<----------------------+
         |  7. Status Update    |                       |
         |<---------------------+                       |
         |     (WebSocket)      |                       |
         |                      |                       |
```

## Communication Sequences

### Command Sequence (e.g., Play, Pause, Stop)

1. **Client Application → AmoraSDK Server**:
   - Client sends HTTP POST request to command endpoint (e.g., `/api/play`)
   - Request format: HTTP POST with optional JSON body

2. **AmoraSDK Server → AmoraOS Player**:
   - Server calls player method (e.g., `player.play()`)
   - Communication is direct method call

3. **AmoraOS Player → AmoraSDK Server**:
   - Player returns command result (success/failure)
   - Communication is method return value

4. **AmoraSDK Server → Client Application**:
   - Server sends HTTP response with command result
   - Response format: JSON with success flag and message
   ```json
   {
     "success": true,
     "message": "Playback started"
   }
   ```

### Status Update Sequence

5. **AmoraSDK Server → AmoraOS Player**:
   - Server periodically polls player for status (e.g., every 1 second)
   - Communication is direct method call to `player.get_status()`

6. **AmoraOS Player → AmoraSDK Server**:
   - Player returns current status data
   - Communication is method return value
   - Data includes playback state, current track, position, etc.

7. **AmoraSDK Server → Client Application**:
   - Server sends status update to all connected WebSocket clients
   - Communication is WebSocket message
   - Message format: JSON status object
   ```json
   {
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
   ```

## Data Structures

### Player Status

The core data structure that flows through the system is the player status:

```typescript
interface PlayerStatus {
  // Current playback state (playing, paused, stopped)
  state: 'play' | 'pause' | 'stop' | 'unknown';
  
  // Current volume level (0-100)
  volume: number;
  
  // Current song information (null if no song is playing)
  current_song?: {
    // Song title
    title: string;
    
    // Artist name
    artist: string;
    
    // Album name
    album: string;
    
    // File path
    file: string;
    
    // Song duration in seconds
    duration: number;
    
    // Current position in seconds
    position: number;
  } | null;
  
  // Current playlist name (null if no playlist is active)
  playlist?: string | null;
}
```

### Command Response

When a command is executed, the response follows this structure:

```typescript
interface CommandResponse {
  // Whether the command was successful
  success: boolean;
  
  // Response message
  message: string;
}
```

### Playlists Response

When requesting available playlists:

```typescript
interface PlaylistsResponse {
  // List of available playlists
  playlists: string[];
}
```

## WebSocket Protocol

The WebSocket connection follows a simple protocol:

1. **Connection**: Client connects to `ws://server-address:8000/ws`
2. **Server → Client**: Server sends status updates as JSON strings
3. **Reconnection**: Client automatically reconnects if connection is lost

There is currently no client-to-server communication over WebSocket; all commands are sent via HTTP API.

## Error Handling

### HTTP API Errors

- **4xx errors**: Client errors (invalid request, etc.)
- **5xx errors**: Server errors (player not available, etc.)

Error responses follow this format:
```json
{
  "detail": "Error message"
}
```

### WebSocket Errors

- **Connection failures**: Client automatically attempts to reconnect
- **Parse errors**: Client logs error and ignores malformed messages
