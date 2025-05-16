/**
 * Amora Music Player Web App Example
 * 
 * This example demonstrates how to use the Amora Client SDK in a web application
 * to control a music player device through MQTT.
 */

// Use a placeholder image for album art when none is available
const PLACEHOLDER_IMAGE = 'placeholder-album.jpg';

// Get DOM elements
const connectionStatusEl = document.getElementById('connectionStatus');
const albumArtEl = document.getElementById('albumArt');
const songTitleEl = document.getElementById('songTitle');
const songArtistEl = document.getElementById('songArtist');
const songAlbumEl = document.getElementById('songAlbum');
const progressBarEl = document.getElementById('progressBar');
const currentTimeEl = document.getElementById('currentTime');
const durationEl = document.getElementById('duration');
const prevButtonEl = document.getElementById('prevButton');
const playPauseButtonEl = document.getElementById('playPauseButton');
const playPauseIconEl = document.getElementById('playPauseIcon');
const stopButtonEl = document.getElementById('stopButton');
const nextButtonEl = document.getElementById('nextButton');
const volumeSliderEl = document.getElementById('volumeSlider');
const volumeValueEl = document.getElementById('volumeValue');
const repeatCheckEl = document.getElementById('repeatCheck');
const randomCheckEl = document.getElementById('randomCheck');
const playlistSelectEl = document.getElementById('playlistSelect');
const loadPlaylistButtonEl = document.getElementById('loadPlaylistButton');
const playlistItemsEl = document.getElementById('playlistItems');
const brokerUrlEl = document.getElementById('brokerUrl');
const brokerPortEl = document.getElementById('brokerPort');
const deviceIdEl = document.getElementById('deviceId');
const connectButtonEl = document.getElementById('connectButton');
const disconnectButtonEl = document.getElementById('disconnectButton');

// Create a variable to hold the client instance
let amoraClient = null;

// Format time in MM:SS format
function formatTime(seconds) {
  if (seconds === undefined || seconds === null) {
    return '0:00';
  }
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Update the UI with player status
function updatePlayerStatus(status) {
  // Update player state
  if (status.state === AmoraSDK.PlayerState.PLAYING) {
    playPauseIconEl.className = 'bi bi-pause-fill';
    playPauseButtonEl.textContent = ' Pause';
  } else {
    playPauseIconEl.className = 'bi bi-play-fill';
    playPauseButtonEl.textContent = ' Play';
  }
  
  // Update current song
  if (status.currentSong) {
    songTitleEl.textContent = status.currentSong.title || 'Unknown Title';
    songArtistEl.textContent = status.currentSong.artist || 'Unknown Artist';
    songAlbumEl.textContent = status.currentSong.album || 'Unknown Album';
    
    // Update album art
    if (status.currentSong.albumArt) {
      albumArtEl.src = status.currentSong.albumArt;
    } else {
      albumArtEl.src = PLACEHOLDER_IMAGE;
    }
    
    // Update duration
    if (status.currentSong.duration) {
      durationEl.textContent = formatTime(status.currentSong.duration);
    } else {
      durationEl.textContent = '0:00';
    }
  } else {
    songTitleEl.textContent = 'No song playing';
    songArtistEl.textContent = '-';
    songAlbumEl.textContent = '-';
    albumArtEl.src = PLACEHOLDER_IMAGE;
    durationEl.textContent = '0:00';
  }
  
  // Update position
  if (status.position !== undefined && status.currentSong && status.currentSong.duration) {
    const percent = (status.position / status.currentSong.duration) * 100;
    progressBarEl.style.width = `${percent}%`;
    currentTimeEl.textContent = formatTime(status.position);
  } else {
    progressBarEl.style.width = '0%';
    currentTimeEl.textContent = '0:00';
  }
  
  // Update volume
  volumeSliderEl.value = status.volume;
  volumeValueEl.textContent = status.volume;
  
  // Update repeat and random
  repeatCheckEl.checked = status.repeat;
  randomCheckEl.checked = status.random;
}

// Update the playlist UI
function updatePlaylistUI(playlists) {
  // Clear the playlist select
  playlistSelectEl.innerHTML = '<option value="">Select a playlist</option>';
  
  // Add playlists to the select
  playlists.forEach(playlist => {
    const option = document.createElement('option');
    option.value = playlist.name;
    option.textContent = playlist.name;
    playlistSelectEl.appendChild(option);
  });
  
  // Update the current playlist items
  const currentPlaylist = playlists.find(p => p.items.some(i => i.isCurrent));
  
  if (currentPlaylist && currentPlaylist.items.length > 0) {
    playlistItemsEl.innerHTML = '';
    
    currentPlaylist.items.forEach((item, index) => {
      const li = document.createElement('li');
      li.className = `list-group-item playlist-item ${item.isCurrent ? 'active' : ''}`;
      li.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <strong>${item.title || 'Unknown Title'}</strong><br>
            <small>${item.artist || 'Unknown Artist'} - ${item.album || 'Unknown Album'}</small>
          </div>
          <span class="badge bg-primary rounded-pill">${formatTime(item.duration)}</span>
        </div>
      `;
      
      // Add click handler to play this track
      li.addEventListener('click', () => {
        if (amoraClient) {
          amoraClient.playTrack(index).catch(handleError);
        }
      });
      
      playlistItemsEl.appendChild(li);
    });
  } else {
    playlistItemsEl.innerHTML = '<li class="list-group-item">No items in playlist</li>';
  }
}

// Update connection status UI
function updateConnectionStatus(status) {
  connectionStatusEl.textContent = status;
  connectionStatusEl.className = `connection-status ${status.toLowerCase()}`;
  
  // Update button states
  if (status === 'Connected') {
    connectButtonEl.disabled = true;
    disconnectButtonEl.disabled = false;
    prevButtonEl.disabled = false;
    playPauseButtonEl.disabled = false;
    stopButtonEl.disabled = false;
    nextButtonEl.disabled = false;
    volumeSliderEl.disabled = false;
    repeatCheckEl.disabled = false;
    randomCheckEl.disabled = false;
    loadPlaylistButtonEl.disabled = false;
  } else {
    connectButtonEl.disabled = status === 'Connecting';
    disconnectButtonEl.disabled = status !== 'Connected';
    prevButtonEl.disabled = true;
    playPauseButtonEl.disabled = true;
    stopButtonEl.disabled = true;
    nextButtonEl.disabled = true;
    volumeSliderEl.disabled = true;
    repeatCheckEl.disabled = true;
    randomCheckEl.disabled = true;
    loadPlaylistButtonEl.disabled = true;
  }
}

// Handle errors
function handleError(error) {
  console.error('Error:', error);
  alert(`Error: ${error.message}`);
}

// Connect to the MQTT broker
async function connect() {
  try {
    // Get connection parameters from the form
    const brokerUrl = brokerUrlEl.value;
    const brokerPort = parseInt(brokerPortEl.value, 10);
    const deviceId = deviceIdEl.value;
    
    // Validate input
    if (!brokerUrl) {
      alert('Please enter a broker URL');
      return;
    }
    
    if (isNaN(brokerPort) || brokerPort <= 0) {
      alert('Please enter a valid broker port');
      return;
    }
    
    if (!deviceId) {
      alert('Please enter a device ID');
      return;
    }
    
    // Update connection status
    updateConnectionStatus('Connecting');
    
    // Create client configuration
    const config = {
      brokerUrl,
      port: brokerPort,
      deviceId,
      connectionOptions: {
        keepAlive: 60,
        cleanSession: true,
        reconnectOnFailure: true
      }
    };
    
    // Create client instance
    amoraClient = new AmoraSDK.AmoraClient(config);
    
    // Set up event listeners
    amoraClient.on(AmoraSDK.EventType.CONNECTION_CHANGE, (status) => {
      if (status === AmoraSDK.ConnectionStatus.CONNECTED) {
        updateConnectionStatus('Connected');
      } else if (status === AmoraSDK.ConnectionStatus.CONNECTING) {
        updateConnectionStatus('Connecting');
      } else {
        updateConnectionStatus('Disconnected');
      }
    });
    
    amoraClient.on(AmoraSDK.EventType.STATE_CHANGE, () => {
      updatePlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(AmoraSDK.EventType.POSITION_CHANGE, () => {
      updatePlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(AmoraSDK.EventType.VOLUME_CHANGE, () => {
      updatePlayerStatus(amoraClient.getPlayerStatus());
    });
    
    amoraClient.on(AmoraSDK.EventType.PLAYLIST_CHANGE, () => {
      updatePlaylistUI(amoraClient.getPlaylists());
    });
    
    amoraClient.on(AmoraSDK.EventType.ERROR, handleError);
    
    // Connect to the MQTT broker
    await amoraClient.connect();
    
    // Get initial status
    const status = await amoraClient.getStatus();
    updatePlayerStatus(status);
    
    // Get available playlists
    const playlists = await amoraClient.fetchPlaylists();
    updatePlaylistUI(playlists);
  } catch (error) {
    handleError(error);
    updateConnectionStatus('Disconnected');
  }
}

// Disconnect from the MQTT broker
async function disconnect() {
  try {
    if (amoraClient) {
      await amoraClient.disconnect();
      amoraClient = null;
    }
    
    updateConnectionStatus('Disconnected');
  } catch (error) {
    handleError(error);
  }
}

// Set up event listeners for UI elements
connectButtonEl.addEventListener('click', connect);
disconnectButtonEl.addEventListener('click', disconnect);

prevButtonEl.addEventListener('click', () => {
  if (amoraClient) {
    amoraClient.previous().catch(handleError);
  }
});

playPauseButtonEl.addEventListener('click', () => {
  if (amoraClient) {
    const status = amoraClient.getPlayerStatus();
    
    if (status.state === AmoraSDK.PlayerState.PLAYING) {
      amoraClient.pause().catch(handleError);
    } else {
      amoraClient.play().catch(handleError);
    }
  }
});

stopButtonEl.addEventListener('click', () => {
  if (amoraClient) {
    amoraClient.stop().catch(handleError);
  }
});

nextButtonEl.addEventListener('click', () => {
  if (amoraClient) {
    amoraClient.next().catch(handleError);
  }
});

volumeSliderEl.addEventListener('input', () => {
  volumeValueEl.textContent = volumeSliderEl.value;
});

volumeSliderEl.addEventListener('change', () => {
  if (amoraClient) {
    const volume = parseInt(volumeSliderEl.value, 10);
    amoraClient.setVolume(volume).catch(handleError);
  }
});

repeatCheckEl.addEventListener('change', () => {
  if (amoraClient) {
    amoraClient.setRepeat(repeatCheckEl.checked).catch(handleError);
  }
});

randomCheckEl.addEventListener('change', () => {
  if (amoraClient) {
    amoraClient.setRandom(randomCheckEl.checked).catch(handleError);
  }
});

loadPlaylistButtonEl.addEventListener('click', () => {
  if (amoraClient) {
    const playlist = playlistSelectEl.value;
    
    if (playlist) {
      amoraClient.playPlaylist(playlist).catch(handleError);
    }
  }
});

// Initialize the UI
updateConnectionStatus('Disconnected');
