# Amora Music Player Web Application

A minimalist, responsive web frontend for the Amora music system that connects to the MQTT broker through the Amora client SDK.

## Overview

This web application provides a clean, simplified interface for controlling the Amora music player. It allows users to:

- Connect to the MQTT broker
- Control music playback (play, pause, stop, next, previous)
- Adjust volume
- View and select playlists
- See the current playing track and playback status as text
- Toggle repeat and random playback modes

## Setup Instructions

### Prerequisites

- Web server (Apache, Nginx, or any static file server)
- Amora MQTT broker running and accessible
- Amora music player device configured and running

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/jpmarques19/amora-os.git
   cd amora-os
   git checkout feature/web-player-ui
   ```

2. Serve the web application:
   - You can use any static file server. For example, with Python:
     ```bash
     cd web-player
     python -m http.server 8080
     ```
   - Or with Node.js and the `serve` package:
     ```bash
     npm install -g serve
     cd web-player
     serve -s .
     ```

3. Open the application in your browser:
   - Navigate to `http://localhost:8080` (or the port you configured)

### Production Deployment

1. Build the Amora client SDK:
   ```bash
   cd amora-sdk/client
   npm install
   npm run build
   ```

2. Replace the mock SDK with the real one:
   - Update the script tag in `index.html` to point to the actual SDK:
     ```html
     <!-- Replace this line -->
     <script src="js/amora-sdk-mock.js"></script>

     <!-- With this line -->
     <script src="path/to/amora-sdk.min.js"></script>
     ```

3. Deploy the web application to your web server:
   - Copy the entire `web-player` directory to your web server's document root
   - Ensure the server is configured to serve static files

## UI Components

### Connection Panel

The connection panel allows users to configure and establish a connection to the MQTT broker:

- **Broker URL**: The URL or IP address of the MQTT broker
- **Port**: The port number of the MQTT broker (default: 1883)
- **Device ID**: The ID of the Amora player device to control
- **Connect/Disconnect Buttons**: Buttons to establish or terminate the connection

### Player Controls

The player controls provide basic playback functionality:

- **Play/Pause Button**: Toggle between play and pause states
- **Stop Button**: Stop playback completely
- **Previous/Next Buttons**: Navigate between tracks
- **Volume Slider**: Adjust the playback volume
- **Repeat/Random Checkboxes**: Toggle repeat and random playback modes

### Now Playing Display

The now playing display shows information about the current track:

- **Track Title**: Name of the current track
- **Artist**: Artist of the current track
- **Album**: Album of the current track
- **Progress Bar**: Visual representation of the playback progress
- **Time Display**: Current position and total duration of the track

### Playlist Panel

The playlist panel allows users to view and manage playlists:

- **Playlist Selector**: Dropdown to select from available playlists
- **Load Playlist Button**: Button to load the selected playlist
- **Current Playlist**: List of tracks in the current playlist
- **Track Items**: Clickable items to select and play specific tracks

## Integration with Amora Client SDK

This web application is designed to integrate with the Amora client SDK for communication with the MQTT broker. The integration points are:

### Connection Management

- `AmoraClient` class is used to establish and manage the connection to the MQTT broker
- Connection status events are handled to update the UI accordingly

### Player Control

- SDK methods like `play()`, `pause()`, `stop()`, `next()`, and `previous()` are used to control playback
- Volume and playback mode settings are controlled through the SDK

### Status Updates

- The application listens for status update events from the SDK to keep the UI in sync with the player state
- Events include state changes, position updates, volume changes, and playlist changes

### Playlist Management

- Available playlists are fetched from the SDK
- Playlist selection and track selection are handled through the SDK

## Development Notes

During development, a mock implementation of the Amora SDK is used to simulate the behavior of the real SDK. This allows for testing and development without an actual MQTT broker connection.

In a production environment, the mock SDK should be replaced with the actual Amora client SDK.

## Browser Compatibility

The web application is designed to work with modern browsers, including:

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Responsive Design

The application uses a responsive design approach to ensure it works well on various devices:

- Desktop: Full layout with sidebar and main content
- Tablet: Adjusted layout with optimized spacing
- Mobile: Stacked layout with touch-friendly controls
