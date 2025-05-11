# AmoraSDK Client Application Development Guide

## Overview

This guide provides instructions for developing client applications that use the AmoraSDK with Azure IoT Hub and Event Hub for device control and real-time status synchronization.

## Prerequisites

- Node.js 14 or later
- npm or yarn
- Azure IoT Hub connection string with service permissions
- Azure Event Hub connection string
- Device ID registered in IoT Hub

## Client SDK Installation

```bash
# Using npm
npm install amora-sdk-client

# Or using yarn
yarn add amora-sdk-client
```

## Basic Usage

```typescript
import { AmoraClient } from 'amora-sdk-client';

// Create client instance
const client = new AmoraClient(
  'YOUR_IOT_HUB_CONNECTION_STRING',
  'YOUR_EVENT_HUB_CONNECTION_STRING',
  'amora-player-001'
);

// Connect to Azure services
await client.connect();

// Listen for status updates
client.onStatusUpdate((status) => {
  console.log('Player status:', status);
});

// Control the player
await client.play();
await client.pause();
await client.next();
await client.previous();
await client.stop();
await client.setVolume(80);

// Get playlists
const playlists = await client.getPlaylists();
console.log('Available playlists:', playlists);

// Disconnect when done
await client.disconnect();
```

## React Integration Example

Here's an example of integrating the AmoraSDK client with a React application:

```tsx
import React, { useState, useEffect } from 'react';
import { AmoraClient, PlayerStatus } from 'amora-sdk-client';

// Configuration
const IOT_HUB_CONNECTION_STRING = 'YOUR_IOT_HUB_CONNECTION_STRING';
const EVENT_HUB_CONNECTION_STRING = 'YOUR_EVENT_HUB_CONNECTION_STRING';
const DEVICE_ID = 'amora-player-001';

const Player: React.FC = () => {
  const [client, setClient] = useState<AmoraClient | null>(null);
  const [status, setStatus] = useState<PlayerStatus>({
    state: 'unknown',
    volume: 0,
    current_song: null,
    playlist: null,
  });
  const [connected, setConnected] = useState(false);

  // Initialize client
  useEffect(() => {
    const initClient = async () => {
      const newClient = new AmoraClient(
        IOT_HUB_CONNECTION_STRING,
        EVENT_HUB_CONNECTION_STRING,
        DEVICE_ID
      );
      
      // Register status update callback
      newClient.onStatusUpdate(setStatus);
      
      // Register connection status callback
      newClient.onConnectionStatus(setConnected);
      
      // Connect to Azure services
      try {
        await newClient.connect();
        setClient(newClient);
      } catch (error) {
        console.error('Failed to connect:', error);
      }
    };
    
    initClient();
    
    // Clean up on unmount
    return () => {
      if (client) {
        client.disconnect();
      }
    };
  }, []);

  // Handle play/pause button click
  const handlePlayPause = async () => {
    if (!client) return;
    
    if (status.state === 'play') {
      await client.pause();
    } else {
      await client.play();
    }
  };

  // Handle stop button click
  const handleStop = async () => {
    if (!client) return;
    await client.stop();
  };

  // Handle next button click
  const handleNext = async () => {
    if (!client) return;
    await client.next();
  };

  // Handle previous button click
  const handlePrevious = async () => {
    if (!client) return;
    await client.previous();
  };

  // Handle volume change
  const handleVolumeChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!client) return;
    const volume = parseInt(e.target.value, 10);
    await client.setVolume(volume);
  };

  // Format time in seconds to MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="player">
      <div className="connection-status">
        {connected ? 'Connected' : 'Disconnected'}
      </div>
      
      <div className="now-playing">
        {status.current_song ? (
          <>
            <h3>{status.current_song.title}</h3>
            <p>{status.current_song.artist} • {status.current_song.album}</p>
            
            <div className="progress">
              <span>{formatTime(status.current_song.position)}</span>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{ 
                    width: `${(status.current_song.position / status.current_song.duration) * 100}%` 
                  }}
                />
              </div>
              <span>{formatTime(status.current_song.duration)}</span>
            </div>
          </>
        ) : (
          <p>No track playing</p>
        )}
      </div>
      
      <div className="controls">
        <button onClick={handlePrevious}>Previous</button>
        <button onClick={handlePlayPause}>
          {status.state === 'play' ? 'Pause' : 'Play'}
        </button>
        <button onClick={handleStop}>Stop</button>
        <button onClick={handleNext}>Next</button>
      </div>
      
      <div className="volume">
        <span>Volume: {status.volume}%</span>
        <input
          type="range"
          min="0"
          max="100"
          value={status.volume}
          onChange={handleVolumeChange}
        />
      </div>
    </div>
  );
};

export default Player;
```

## Angular Integration Example

Here's an example of integrating the AmoraSDK client with an Angular application:

```typescript
// player.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { AmoraClient, PlayerStatus } from 'amora-sdk-client';

@Component({
  selector: 'app-player',
  templateUrl: './player.component.html',
  styleUrls: ['./player.component.css']
})
export class PlayerComponent implements OnInit, OnDestroy {
  private client: AmoraClient;
  public status: PlayerStatus = {
    state: 'unknown',
    volume: 0,
    current_song: null,
    playlist: null
  };
  public connected = false;

  constructor() {
    // Initialize client
    this.client = new AmoraClient(
      'YOUR_IOT_HUB_CONNECTION_STRING',
      'YOUR_EVENT_HUB_CONNECTION_STRING',
      'amora-player-001'
    );
  }

  async ngOnInit() {
    // Register status update callback
    this.client.onStatusUpdate((status) => {
      this.status = status;
    });
    
    // Register connection status callback
    this.client.onConnectionStatus((connected) => {
      this.connected = connected;
    });
    
    // Connect to Azure services
    try {
      await this.client.connect();
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  }

  ngOnDestroy() {
    // Disconnect when component is destroyed
    this.client.disconnect();
  }

  async playPause() {
    if (this.status.state === 'play') {
      await this.client.pause();
    } else {
      await this.client.play();
    }
  }

  async stop() {
    await this.client.stop();
  }

  async next() {
    await this.client.next();
  }

  async previous() {
    await this.client.previous();
  }

  async setVolume(event: any) {
    const volume = event.target.value;
    await this.client.setVolume(volume);
  }

  formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
}
```

```html
<!-- player.component.html -->
<div class="player">
  <div class="connection-status" [class.connected]="connected">
    {{ connected ? 'Connected' : 'Disconnected' }}
  </div>
  
  <div class="now-playing">
    <ng-container *ngIf="status.current_song; else noTrack">
      <h3>{{ status.current_song.title }}</h3>
      <p>{{ status.current_song.artist }} • {{ status.current_song.album }}</p>
      
      <div class="progress">
        <span>{{ formatTime(status.current_song.position) }}</span>
        <div class="progress-bar">
          <div 
            class="progress-bar-fill" 
            [style.width.%]="(status.current_song.position / status.current_song.duration) * 100"
          ></div>
        </div>
        <span>{{ formatTime(status.current_song.duration) }}</span>
      </div>
    </ng-container>
    
    <ng-template #noTrack>
      <p>No track playing</p>
    </ng-template>
  </div>
  
  <div class="controls">
    <button (click)="previous()">Previous</button>
    <button (click)="playPause()">
      {{ status.state === 'play' ? 'Pause' : 'Play' }}
    </button>
    <button (click)="stop()">Stop</button>
    <button (click)="next()">Next</button>
  </div>
  
  <div class="volume">
    <span>Volume: {{ status.volume }}%</span>
    <input
      type="range"
      min="0"
      max="100"
      [value]="status.volume"
      (input)="setVolume($event)"
    />
  </div>
</div>
```

## Best Practices

1. **Error Handling**: Always handle errors from API calls and provide appropriate feedback to users.

2. **Connection Management**: Implement reconnection logic for handling network interruptions.

3. **State Management**: Use a state management library (Redux, MobX, NgRx) for complex applications.

4. **Caching**: Cache device twin data to reduce API calls and improve responsiveness.

5. **Security**: Store connection strings securely and consider using Azure AD authentication for production applications.

6. **Testing**: Implement unit tests for components that interact with the AmoraSDK client.

7. **Offline Support**: Implement offline support for mobile applications by caching commands and syncing when online.
