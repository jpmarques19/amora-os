# Integrating Amora Client SDK into Web Applications

This guide explains how to integrate the Amora Client SDK into web applications to control music player devices through MQTT.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Integration](#basic-integration)
- [Advanced Integration](#advanced-integration)
- [Using with Modern Frameworks](#using-with-modern-frameworks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before integrating the Amora Client SDK into your web application, ensure you have:

1. An Amora music player device running and connected to an MQTT broker
2. The MQTT broker accessible from your web application (consider CORS if using WebSockets)
3. Basic knowledge of JavaScript and web development

## Installation

### Using NPM (Recommended for Modern Web Apps)

If you're using a build system like Webpack, Rollup, or Parcel:

```bash
npm install amora-client-sdk
```

Then import it in your code:

```javascript
import { AmoraClient, EventType } from 'amora-client-sdk';
```

### Using CDN (For Traditional Web Pages)

Add the following script tag to your HTML:

```html
<script src="https://cdn.jsdelivr.net/npm/amora-client-sdk/dist/bundle.js"></script>
```

This will expose the SDK as a global variable `AmoraSDK`:

```javascript
const { AmoraClient, EventType } = AmoraSDK;
```

## Basic Integration

### 1. Create the Client

```javascript
// Configuration
const config = {
  brokerUrl: 'localhost',  // MQTT broker URL
  port: 1883,              // MQTT broker port
  deviceId: 'amora-player-001'  // Device ID to connect to
};

// Create client instance
const client = new AmoraClient(config);
```

### 2. Set Up Event Listeners

```javascript
// Listen for player state changes
client.on(EventType.STATE_CHANGE, (state) => {
  console.log(`Player state changed: ${state}`);
  updatePlayerUI(client.getPlayerStatus());
});

// Listen for position changes
client.on(EventType.POSITION_CHANGE, (position) => {
  updateProgressBar(position);
});

// Listen for volume changes
client.on(EventType.VOLUME_CHANGE, (volume) => {
  updateVolumeUI(volume);
});

// Listen for playlist changes
client.on(EventType.PLAYLIST_CHANGE, (playlists) => {
  updatePlaylistUI(playlists);
});

// Listen for connection changes
client.on(EventType.CONNECTION_CHANGE, (status) => {
  updateConnectionUI(status);
});

// Listen for errors
client.on(EventType.ERROR, (error) => {
  showErrorMessage(error.message);
});
```

### 3. Connect to the MQTT Broker

```javascript
async function connectToPlayer() {
  try {
    await client.connect();
    console.log('Connected to player!');
    
    // Get initial status
    const status = await client.getStatus();
    updatePlayerUI(status);
    
    // Get available playlists
    const playlists = await client.fetchPlaylists();
    updatePlaylistUI(playlists);
  } catch (error) {
    console.error('Connection error:', error.message);
    showErrorMessage(`Failed to connect: ${error.message}`);
  }
}

// Call this function when the user clicks a connect button
document.getElementById('connectButton').addEventListener('click', connectToPlayer);
```

### 4. Control the Player

```javascript
// Play button
document.getElementById('playButton').addEventListener('click', async () => {
  try {
    await client.play();
  } catch (error) {
    showErrorMessage(`Failed to play: ${error.message}`);
  }
});

// Pause button
document.getElementById('pauseButton').addEventListener('click', async () => {
  try {
    await client.pause();
  } catch (error) {
    showErrorMessage(`Failed to pause: ${error.message}`);
  }
});

// Stop button
document.getElementById('stopButton').addEventListener('click', async () => {
  try {
    await client.stop();
  } catch (error) {
    showErrorMessage(`Failed to stop: ${error.message}`);
  }
});

// Next button
document.getElementById('nextButton').addEventListener('click', async () => {
  try {
    await client.next();
  } catch (error) {
    showErrorMessage(`Failed to skip to next track: ${error.message}`);
  }
});

// Previous button
document.getElementById('prevButton').addEventListener('click', async () => {
  try {
    await client.previous();
  } catch (error) {
    showErrorMessage(`Failed to go to previous track: ${error.message}`);
  }
});

// Volume slider
document.getElementById('volumeSlider').addEventListener('change', async (event) => {
  try {
    const volume = parseInt(event.target.value, 10);
    await client.setVolume(volume);
  } catch (error) {
    showErrorMessage(`Failed to set volume: ${error.message}`);
  }
});
```

### 5. Update the UI

```javascript
function updatePlayerUI(status) {
  // Update player state
  const stateElement = document.getElementById('playerState');
  stateElement.textContent = status.state;
  
  // Update current song
  if (status.currentSong) {
    document.getElementById('songTitle').textContent = status.currentSong.title;
    document.getElementById('songArtist').textContent = status.currentSong.artist;
    document.getElementById('songAlbum').textContent = status.currentSong.album;
    
    // Update album art if available
    if (status.currentSong.albumArt) {
      document.getElementById('albumArt').src = status.currentSong.albumArt;
    } else {
      document.getElementById('albumArt').src = 'placeholder.jpg';
    }
    
    // Update duration
    if (status.currentSong.duration) {
      document.getElementById('duration').textContent = formatTime(status.currentSong.duration);
    }
  } else {
    document.getElementById('songTitle').textContent = 'No song playing';
    document.getElementById('songArtist').textContent = '';
    document.getElementById('songAlbum').textContent = '';
    document.getElementById('albumArt').src = 'placeholder.jpg';
    document.getElementById('duration').textContent = '0:00';
  }
  
  // Update volume
  document.getElementById('volumeSlider').value = status.volume;
  document.getElementById('volumeValue').textContent = `${status.volume}%`;
  
  // Update repeat and random
  document.getElementById('repeatCheck').checked = status.repeat;
  document.getElementById('randomCheck').checked = status.random;
}

function updateProgressBar(position) {
  const status = client.getPlayerStatus();
  
  if (status.currentSong && status.currentSong.duration) {
    const percent = (position / status.currentSong.duration) * 100;
    document.getElementById('progressBar').style.width = `${percent}%`;
    document.getElementById('currentTime').textContent = formatTime(position);
  }
}

function updateVolumeUI(volume) {
  document.getElementById('volumeSlider').value = volume;
  document.getElementById('volumeValue').textContent = `${volume}%`;
}

function updatePlaylistUI(playlists) {
  const playlistSelect = document.getElementById('playlistSelect');
  playlistSelect.innerHTML = '<option value="">Select a playlist</option>';
  
  playlists.forEach(playlist => {
    const option = document.createElement('option');
    option.value = playlist.name;
    option.textContent = playlist.name;
    playlistSelect.appendChild(option);
  });
  
  // Update current playlist items
  const currentPlaylist = playlists.find(p => p.items.some(i => i.isCurrent));
  const playlistItems = document.getElementById('playlistItems');
  
  if (currentPlaylist && currentPlaylist.items.length > 0) {
    playlistItems.innerHTML = '';
    
    currentPlaylist.items.forEach((item, index) => {
      const li = document.createElement('li');
      li.className = `playlist-item ${item.isCurrent ? 'active' : ''}`;
      li.innerHTML = `
        <div class="song-info">
          <strong>${item.title}</strong>
          <div>${item.artist} - ${item.album}</div>
          <div>${formatTime(item.duration)}</div>
        </div>
      `;
      
      li.addEventListener('click', () => {
        client.playTrack(index).catch(error => {
          showErrorMessage(`Failed to play track: ${error.message}`);
        });
      });
      
      playlistItems.appendChild(li);
    });
  } else {
    playlistItems.innerHTML = '<li>No items in playlist</li>';
  }
}

function updateConnectionUI(status) {
  const connectionStatus = document.getElementById('connectionStatus');
  connectionStatus.textContent = status;
  connectionStatus.className = `connection-status ${status.toLowerCase()}`;
  
  // Update button states
  document.getElementById('connectButton').disabled = status === 'connected' || status === 'connecting';
  document.getElementById('disconnectButton').disabled = status !== 'connected';
  
  // Enable/disable player controls
  const playerControls = document.querySelectorAll('.player-control');
  playerControls.forEach(control => {
    control.disabled = status !== 'connected';
  });
}

function showErrorMessage(message) {
  const errorElement = document.getElementById('errorMessage');
  errorElement.textContent = message;
  errorElement.style.display = 'block';
  
  // Hide after 5 seconds
  setTimeout(() => {
    errorElement.style.display = 'none';
  }, 5000);
}

function formatTime(seconds) {
  if (!seconds) return '0:00';
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
```

### 6. Disconnect When Done

```javascript
async function disconnectFromPlayer() {
  try {
    await client.disconnect();
    console.log('Disconnected from player');
    updateConnectionUI('disconnected');
  } catch (error) {
    console.error('Disconnection error:', error.message);
  }
}

// Call this function when the user clicks a disconnect button
document.getElementById('disconnectButton').addEventListener('click', disconnectFromPlayer);

// Also disconnect when the page is unloaded
window.addEventListener('beforeunload', () => {
  if (client && client.getConnectionStatus() === 'connected') {
    client.disconnect().catch(console.error);
  }
});
```

## Advanced Integration

### Handling Connection Issues

For a robust web application, you should handle connection issues gracefully:

```javascript
client.on(EventType.CONNECTION_CHANGE, (status) => {
  updateConnectionUI(status);
  
  if (status === 'disconnected') {
    // Show reconnect button or attempt automatic reconnection
    document.getElementById('reconnectButton').style.display = 'block';
  } else {
    document.getElementById('reconnectButton').style.display = 'none';
  }
});

// Implement a reconnect function
async function reconnect() {
  try {
    document.getElementById('reconnectButton').disabled = true;
    document.getElementById('reconnectButton').textContent = 'Reconnecting...';
    
    await client.connect();
    
    document.getElementById('reconnectButton').disabled = false;
    document.getElementById('reconnectButton').textContent = 'Reconnect';
  } catch (error) {
    console.error('Reconnection error:', error.message);
    document.getElementById('reconnectButton').disabled = false;
    document.getElementById('reconnectButton').textContent = 'Reconnect';
    showErrorMessage(`Failed to reconnect: ${error.message}`);
  }
}

document.getElementById('reconnectButton').addEventListener('click', reconnect);
```

### Implementing a Progress Bar with Seeking

```javascript
// Make the progress bar interactive for seeking
const progressContainer = document.getElementById('progressContainer');
progressContainer.addEventListener('click', async (event) => {
  try {
    const status = client.getPlayerStatus();
    
    if (status.currentSong && status.currentSong.duration) {
      // Calculate the click position as a percentage
      const rect = progressContainer.getBoundingClientRect();
      const clickPosition = (event.clientX - rect.left) / rect.width;
      
      // Convert to seconds
      const seekTime = clickPosition * status.currentSong.duration;
      
      // Send seek command
      await client.seek(seekTime);
    }
  } catch (error) {
    showErrorMessage(`Failed to seek: ${error.message}`);
  }
});
```

### Playlist Management

```javascript
// Add a track to the playlist
async function addTrackToPlaylist(track, playlist) {
  try {
    await client.addTrack(track, playlist);
    showMessage('Track added to playlist');
  } catch (error) {
    showErrorMessage(`Failed to add track: ${error.message}`);
  }
}

// Remove a track from the playlist
async function removeTrackFromPlaylist(trackIndex, playlist) {
  try {
    await client.removeTrack(trackIndex, playlist);
    showMessage('Track removed from playlist');
  } catch (error) {
    showErrorMessage(`Failed to remove track: ${error.message}`);
  }
}

// Reorder tracks in the playlist
async function reorderTrack(fromIndex, toIndex, playlist) {
  try {
    await client.reorderTrack(fromIndex, toIndex, playlist);
    showMessage('Playlist reordered');
  } catch (error) {
    showErrorMessage(`Failed to reorder playlist: ${error.message}`);
  }
}
```

## Using with Modern Frameworks

### React

```jsx
import React, { useState, useEffect } from 'react';
import { AmoraClient, EventType, ConnectionStatus, PlayerState } from 'amora-client-sdk';

function AmoraPlayer() {
  const [client, setClient] = useState(null);
  const [connected, setConnected] = useState(false);
  const [playerStatus, setPlayerStatus] = useState({
    state: PlayerState.STOPPED,
    volume: 0,
    repeat: false,
    random: false
  });
  const [playlists, setPlaylists] = useState([]);
  
  // Initialize client
  useEffect(() => {
    const amoraClient = new AmoraClient({
      brokerUrl: 'localhost',
      port: 1883,
      deviceId: 'amora-player-001'
    });
    
    // Set up event listeners
    amoraClient.on(EventType.STATE_CHANGE, () => {
      setPlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(EventType.POSITION_CHANGE, () => {
      setPlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(EventType.VOLUME_CHANGE, () => {
      setPlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(EventType.PLAYLIST_CHANGE, () => {
      setPlaylists(amoraClient.getPlaylists());
    });
    
    amoraClient.on(EventType.CONNECTION_CHANGE, (status) => {
      setConnected(status === ConnectionStatus.CONNECTED);
    });
    
    setClient(amoraClient);
    
    // Clean up on unmount
    return () => {
      if (amoraClient && amoraClient.getConnectionStatus() === ConnectionStatus.CONNECTED) {
        amoraClient.disconnect().catch(console.error);
      }
    };
  }, []);
  
  // Connect to the player
  const connect = async () => {
    if (!client) return;
    
    try {
      await client.connect();
      await client.fetchPlaylists();
    } catch (error) {
      console.error('Connection error:', error);
    }
  };
  
  // Disconnect from the player
  const disconnect = async () => {
    if (!client) return;
    
    try {
      await client.disconnect();
    } catch (error) {
      console.error('Disconnection error:', error);
    }
  };
  
  // Player controls
  const play = () => client?.play().catch(console.error);
  const pause = () => client?.pause().catch(console.error);
  const stop = () => client?.stop().catch(console.error);
  const next = () => client?.next().catch(console.error);
  const previous = () => client?.previous().catch(console.error);
  const setVolume = (volume) => client?.setVolume(volume).catch(console.error);
  
  return (
    <div className="amora-player">
      <div className="connection-controls">
        <button onClick={connect} disabled={connected}>Connect</button>
        <button onClick={disconnect} disabled={!connected}>Disconnect</button>
        <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      <div className="player-info">
        <h2>{playerStatus.currentSong?.title || 'No song playing'}</h2>
        <p>{playerStatus.currentSong?.artist || ''} - {playerStatus.currentSong?.album || ''}</p>
        
        <div className="progress-bar">
          <div 
            className="progress" 
            style={{ 
              width: `${playerStatus.position && playerStatus.currentSong?.duration ? 
                (playerStatus.position / playerStatus.currentSong.duration) * 100 : 0}%` 
            }}
          ></div>
        </div>
        
        <div className="controls">
          <button onClick={previous} disabled={!connected}>Previous</button>
          {playerStatus.state === PlayerState.PLAYING ? (
            <button onClick={pause} disabled={!connected}>Pause</button>
          ) : (
            <button onClick={play} disabled={!connected}>Play</button>
          )}
          <button onClick={stop} disabled={!connected}>Stop</button>
          <button onClick={next} disabled={!connected}>Next</button>
        </div>
        
        <div className="volume-control">
          <label>
            Volume: {playerStatus.volume}%
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={playerStatus.volume} 
              onChange={(e) => setVolume(parseInt(e.target.value, 10))}
              disabled={!connected}
            />
          </label>
        </div>
      </div>
      
      <div className="playlists">
        <h3>Playlists</h3>
        <select 
          onChange={(e) => client?.playPlaylist(e.target.value).catch(console.error)}
          disabled={!connected}
        >
          <option value="">Select a playlist</option>
          {playlists.map(playlist => (
            <option key={playlist.name} value={playlist.name}>
              {playlist.name}
            </option>
          ))}
        </select>
        
        <div className="current-playlist">
          <h4>Current Playlist</h4>
          <ul>
            {playlists.find(p => p.items.some(i => i.isCurrent))?.items.map((item, index) => (
              <li 
                key={index} 
                className={item.isCurrent ? 'current' : ''}
                onClick={() => client?.playTrack(index).catch(console.error)}
              >
                {item.title} - {item.artist}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default AmoraPlayer;
```

### Vue.js

```vue
<template>
  <div class="amora-player">
    <div class="connection-controls">
      <button @click="connect" :disabled="connected">Connect</button>
      <button @click="disconnect" :disabled="!connected">Disconnect</button>
      <div :class="['status', connected ? 'connected' : 'disconnected']">
        {{ connected ? 'Connected' : 'Disconnected' }}
      </div>
    </div>
    
    <div class="player-info">
      <h2>{{ currentSong?.title || 'No song playing' }}</h2>
      <p>{{ currentSong?.artist || '' }} - {{ currentSong?.album || '' }}</p>
      
      <div class="progress-bar">
        <div 
          class="progress" 
          :style="{ width: progressWidth + '%' }"
        ></div>
      </div>
      
      <div class="controls">
        <button @click="previous" :disabled="!connected">Previous</button>
        <button v-if="playerState === 'playing'" @click="pause" :disabled="!connected">Pause</button>
        <button v-else @click="play" :disabled="!connected">Play</button>
        <button @click="stop" :disabled="!connected">Stop</button>
        <button @click="next" :disabled="!connected">Next</button>
      </div>
      
      <div class="volume-control">
        <label>
          Volume: {{ volume }}%
          <input 
            type="range" 
            min="0" 
            max="100" 
            v-model.number="volume" 
            @change="setVolume"
            :disabled="!connected"
          />
        </label>
      </div>
    </div>
    
    <div class="playlists">
      <h3>Playlists</h3>
      <select 
        @change="playPlaylist"
        :disabled="!connected"
      >
        <option value="">Select a playlist</option>
        <option 
          v-for="playlist in playlists" 
          :key="playlist.name" 
          :value="playlist.name"
        >
          {{ playlist.name }}
        </option>
      </select>
      
      <div class="current-playlist">
        <h4>Current Playlist</h4>
        <ul>
          <li 
            v-for="(item, index) in currentPlaylistItems" 
            :key="index" 
            :class="{ current: item.isCurrent }"
            @click="playTrack(index)"
          >
            {{ item.title }} - {{ item.artist }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { AmoraClient, EventType, ConnectionStatus, PlayerState } from 'amora-client-sdk';

export default {
  data() {
    return {
      client: null,
      connected: false,
      playerState: PlayerState.STOPPED,
      currentSong: null,
      position: 0,
      volume: 0,
      repeat: false,
      random: false,
      playlists: []
    };
  },
  computed: {
    progressWidth() {
      if (this.position && this.currentSong?.duration) {
        return (this.position / this.currentSong.duration) * 100;
      }
      return 0;
    },
    currentPlaylistItems() {
      const currentPlaylist = this.playlists.find(p => p.items.some(i => i.isCurrent));
      return currentPlaylist ? currentPlaylist.items : [];
    }
  },
  created() {
    this.initClient();
  },
  beforeUnmount() {
    this.cleanup();
  },
  methods: {
    initClient() {
      this.client = new AmoraClient({
        brokerUrl: 'localhost',
        port: 1883,
        deviceId: 'amora-player-001'
      });
      
      this.client.on(EventType.STATE_CHANGE, (state) => {
        this.playerState = state;
      });
      
      this.client.on(EventType.POSITION_CHANGE, (position) => {
        this.position = position;
      });
      
      this.client.on(EventType.VOLUME_CHANGE, (volume) => {
        this.volume = volume;
      });
      
      this.client.on(EventType.PLAYLIST_CHANGE, (playlists) => {
        this.playlists = playlists;
      });
      
      this.client.on(EventType.CONNECTION_CHANGE, (status) => {
        this.connected = status === ConnectionStatus.CONNECTED;
      });
      
      this.client.on(EventType.COMMAND_RESPONSE, (response) => {
        if (response.data) {
          if (response.data.currentSong) {
            this.currentSong = response.data.currentSong;
          }
        }
      });
    },
    async connect() {
      try {
        await this.client.connect();
        const status = await this.client.getStatus();
        this.playerState = status.state;
        this.currentSong = status.currentSong;
        this.position = status.position;
        this.volume = status.volume;
        this.repeat = status.repeat;
        this.random = status.random;
        
        await this.client.fetchPlaylists();
      } catch (error) {
        console.error('Connection error:', error);
      }
    },
    async disconnect() {
      try {
        await this.client.disconnect();
      } catch (error) {
        console.error('Disconnection error:', error);
      }
    },
    async play() {
      try {
        await this.client.play();
      } catch (error) {
        console.error('Play error:', error);
      }
    },
    async pause() {
      try {
        await this.client.pause();
      } catch (error) {
        console.error('Pause error:', error);
      }
    },
    async stop() {
      try {
        await this.client.stop();
      } catch (error) {
        console.error('Stop error:', error);
      }
    },
    async next() {
      try {
        await this.client.next();
      } catch (error) {
        console.error('Next error:', error);
      }
    },
    async previous() {
      try {
        await this.client.previous();
      } catch (error) {
        console.error('Previous error:', error);
      }
    },
    async setVolume() {
      try {
        await this.client.setVolume(this.volume);
      } catch (error) {
        console.error('Set volume error:', error);
      }
    },
    async playPlaylist(event) {
      try {
        const playlist = event.target.value;
        if (playlist) {
          await this.client.playPlaylist(playlist);
        }
      } catch (error) {
        console.error('Play playlist error:', error);
      }
    },
    async playTrack(index) {
      try {
        await this.client.playTrack(index);
      } catch (error) {
        console.error('Play track error:', error);
      }
    },
    cleanup() {
      if (this.client && this.client.getConnectionStatus() === ConnectionStatus.CONNECTED) {
        this.client.disconnect().catch(console.error);
      }
    }
  }
};
</script>

<style scoped>
.amora-player {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.status {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 4px;
  margin-left: 10px;
}

.status.connected {
  background-color: #d4edda;
  color: #155724;
}

.status.disconnected {
  background-color: #f8d7da;
  color: #721c24;
}

.progress-bar {
  height: 10px;
  background-color: #e9ecef;
  border-radius: 5px;
  margin: 10px 0;
  overflow: hidden;
}

.progress {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.controls {
  margin: 15px 0;
}

.controls button {
  margin-right: 5px;
}

.current-playlist li {
  cursor: pointer;
  padding: 5px;
}

.current-playlist li.current {
  background-color: #e9ecef;
  font-weight: bold;
}
</style>
```

## Troubleshooting

### MQTT Connection Issues

1. **Browser WebSocket Support**: Ensure your MQTT broker supports WebSockets for browser connections.

2. **CORS Issues**: If your web app is hosted on a different domain than your MQTT broker, you may encounter CORS issues. Configure your MQTT broker to allow cross-origin requests.

3. **Secure WebSockets**: For production applications, use secure WebSockets (WSS) instead of plain WebSockets (WS).

4. **Connection Timeouts**: If connections time out, check network connectivity and firewall settings.

### Common Errors and Solutions

1. **"Failed to connect to MQTT broker"**:
   - Check if the MQTT broker is running
   - Verify the broker URL and port
   - Ensure the broker accepts WebSocket connections

2. **"Command timed out"**:
   - Check if the device is connected to the MQTT broker
   - Verify the device ID is correct
   - Check if the device is responding to commands

3. **"Not connected to MQTT broker"**:
   - Ensure you call `connect()` before sending commands
   - Check the connection status before sending commands

4. **"Unknown command"**:
   - Verify the command is supported by the device
   - Check for typos in the command name

### Debugging Tips

1. **Enable Logging**: The SDK uses console logging. Open your browser's developer tools to see logs.

2. **Check Network Traffic**: Use the Network tab in developer tools to monitor WebSocket traffic.

3. **Test with MQTT Explorer**: Use tools like MQTT Explorer to verify the MQTT broker is working correctly.

4. **Implement Retry Logic**: For unreliable connections, implement retry logic for commands.

```javascript
async function sendCommandWithRetry(command, params, maxRetries = 3) {
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      return await client[command](params);
    } catch (error) {
      retries++;
      
      if (retries >= maxRetries) {
        throw error;
      }
      
      console.log(`Retrying ${command} (${retries}/${maxRetries})...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}

// Usage
try {
  await sendCommandWithRetry('play');
} catch (error) {
  showErrorMessage(`Failed after multiple attempts: ${error.message}`);
}
```
