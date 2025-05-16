/**
 * Amora SDK Mock
 * 
 * This file provides a mock implementation of the Amora SDK for development purposes.
 * In a production environment, this would be replaced with the actual Amora SDK.
 */

// Create a global namespace for the SDK
window.AmoraSDK = (function() {
  // Enums
  const PlayerState = {
    PLAYING: 'playing',
    PAUSED: 'paused',
    STOPPED: 'stopped',
    LOADING: 'loading',
    ERROR: 'error'
  };

  const ConnectionStatus = {
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    ERROR: 'error'
  };

  const EventType = {
    STATE_CHANGE: 'stateChange',
    POSITION_CHANGE: 'positionChange',
    VOLUME_CHANGE: 'volumeChange',
    PLAYLIST_CHANGE: 'playlistChange',
    CONNECTION_CHANGE: 'connectionChange',
    COMMAND_RESPONSE: 'commandResponse',
    ERROR: 'error'
  };

  // Sample data for testing
  const sampleTracks = [
    {
      title: 'Do I',
      artist: 'LEEONA',
      album: 'LEEONA',
      duration: 180,
      file: 'LEEONA_-_LEEONA_-_Do_I.mp3'
    },
    {
      title: 'Jupiter and Mars',
      artist: 'Square a Saw',
      album: 'Planets',
      duration: 240,
      file: 'Square_a_Saw_-_Jupiter_and_Mars.mp3'
    },
    {
      title: 'Host',
      artist: 'Color Out',
      album: 'Potential',
      duration: 210,
      file: 'Color_Out_-_Host.mp3'
    }
  ];

  const samplePlaylists = [
    {
      name: 'Favorites',
      items: sampleTracks.map((track, index) => ({
        ...track,
        position: index,
        isCurrent: index === 0
      }))
    },
    {
      name: 'Recently Added',
      items: sampleTracks.slice().reverse().map((track, index) => ({
        ...track,
        position: index,
        isCurrent: false
      }))
    }
  ];

  /**
   * AmoraClient class - Mock implementation
   */
  class AmoraClient {
    constructor(config) {
      this.config = config;
      this.eventListeners = {};
      this.connectionStatus = ConnectionStatus.DISCONNECTED;
      this.playerStatus = {
        state: PlayerState.STOPPED,
        volume: 50,
        repeat: false,
        random: false,
        position: 0
      };
      this.playlists = [];
      this.currentPlaylist = null;
      this.positionUpdateInterval = null;
    }

    // Event handling
    on(event, listener) {
      if (!this.eventListeners[event]) {
        this.eventListeners[event] = [];
      }
      this.eventListeners[event].push(listener);
      return this;
    }

    off(event, listener) {
      if (this.eventListeners[event]) {
        this.eventListeners[event] = this.eventListeners[event].filter(l => l !== listener);
      }
      return this;
    }

    emit(event, data) {
      if (this.eventListeners[event]) {
        this.eventListeners[event].forEach(listener => listener(data));
      }
    }

    // Connection methods
    async connect() {
      this.emit(EventType.CONNECTION_CHANGE, ConnectionStatus.CONNECTING);
      
      // Simulate connection delay
      return new Promise((resolve) => {
        setTimeout(() => {
          this.connectionStatus = ConnectionStatus.CONNECTED;
          this.emit(EventType.CONNECTION_CHANGE, this.connectionStatus);
          
          // Load sample data
          this.playlists = JSON.parse(JSON.stringify(samplePlaylists));
          this.currentPlaylist = this.playlists[0];
          this.playerStatus.currentSong = this.currentPlaylist.items[0];
          
          resolve();
        }, 1000);
      });
    }

    async disconnect() {
      // Clear position update interval
      if (this.positionUpdateInterval) {
        clearInterval(this.positionUpdateInterval);
        this.positionUpdateInterval = null;
      }
      
      // Update status
      this.connectionStatus = ConnectionStatus.DISCONNECTED;
      this.emit(EventType.CONNECTION_CHANGE, this.connectionStatus);
      
      return Promise.resolve();
    }

    getConnectionStatus() {
      return this.connectionStatus;
    }

    // Player status methods
    getPlayerStatus() {
      return { ...this.playerStatus };
    }

    getPlaylists() {
      return JSON.parse(JSON.stringify(this.playlists));
    }

    // Player control methods
    async play() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.state = PlayerState.PLAYING;
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      
      // Start position update interval
      if (!this.positionUpdateInterval) {
        this.positionUpdateInterval = setInterval(() => {
          if (this.playerStatus.state === PlayerState.PLAYING && this.playerStatus.currentSong) {
            this.playerStatus.position += 1;
            
            // Loop back to start if we reach the end
            if (this.playerStatus.position >= this.playerStatus.currentSong.duration) {
              if (this.playerStatus.repeat) {
                this.playerStatus.position = 0;
              } else {
                this.next();
              }
            }
            
            this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
          }
        }, 1000);
      }
      
      return Promise.resolve();
    }

    async pause() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.state = PlayerState.PAUSED;
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      
      return Promise.resolve();
    }

    async stop() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.state = PlayerState.STOPPED;
      this.playerStatus.position = 0;
      
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
      
      return Promise.resolve();
    }

    async next() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      if (this.currentPlaylist && this.currentPlaylist.items.length > 0) {
        // Find current track
        const currentIndex = this.currentPlaylist.items.findIndex(item => item.isCurrent);
        
        // Calculate next index
        let nextIndex;
        if (this.playerStatus.random) {
          // Random mode - pick a random track
          nextIndex = Math.floor(Math.random() * this.currentPlaylist.items.length);
        } else {
          // Normal mode - go to next track
          nextIndex = (currentIndex + 1) % this.currentPlaylist.items.length;
        }
        
        // Update current track
        this.currentPlaylist.items.forEach((item, index) => {
          item.isCurrent = index === nextIndex;
        });
        
        // Update player status
        this.playerStatus.currentSong = this.currentPlaylist.items[nextIndex];
        this.playerStatus.position = 0;
        
        // Emit events
        this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
        this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
        this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
      }
      
      return Promise.resolve();
    }

    async previous() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      if (this.currentPlaylist && this.currentPlaylist.items.length > 0) {
        // Find current track
        const currentIndex = this.currentPlaylist.items.findIndex(item => item.isCurrent);
        
        // Calculate previous index
        let prevIndex;
        if (this.playerStatus.random) {
          // Random mode - pick a random track
          prevIndex = Math.floor(Math.random() * this.currentPlaylist.items.length);
        } else {
          // Normal mode - go to previous track
          prevIndex = (currentIndex - 1 + this.currentPlaylist.items.length) % this.currentPlaylist.items.length;
        }
        
        // Update current track
        this.currentPlaylist.items.forEach((item, index) => {
          item.isCurrent = index === prevIndex;
        });
        
        // Update player status
        this.playerStatus.currentSong = this.currentPlaylist.items[prevIndex];
        this.playerStatus.position = 0;
        
        // Emit events
        this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
        this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
        this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
      }
      
      return Promise.resolve();
    }

    async setVolume(volume) {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.volume = volume;
      this.emit(EventType.VOLUME_CHANGE, this.playerStatus.volume);
      
      return Promise.resolve();
    }

    async setRepeat(repeat) {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.repeat = repeat;
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      
      return Promise.resolve();
    }

    async setRandom(random) {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      this.playerStatus.random = random;
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      
      return Promise.resolve();
    }

    async getStatus() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      return Promise.resolve({ ...this.playerStatus });
    }

    async fetchPlaylists() {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      return Promise.resolve(JSON.parse(JSON.stringify(this.playlists)));
    }

    async playPlaylist(playlistName) {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      // Find playlist
      const playlist = this.playlists.find(p => p.name === playlistName);
      if (!playlist) {
        throw new Error(`Playlist "${playlistName}" not found`);
      }
      
      // Set as current playlist
      this.currentPlaylist = playlist;
      
      // Set first track as current
      this.playlists.forEach(p => {
        p.items.forEach(item => {
          item.isCurrent = p === playlist && item.position === 0;
        });
      });
      
      // Update player status
      this.playerStatus.currentSong = playlist.items[0];
      this.playerStatus.position = 0;
      this.playerStatus.state = PlayerState.PLAYING;
      
      // Emit events
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
      this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
      this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
      
      return Promise.resolve();
    }

    async playTrack(trackIndex) {
      if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
        throw new Error('Not connected');
      }
      
      if (this.currentPlaylist && trackIndex >= 0 && trackIndex < this.currentPlaylist.items.length) {
        // Update current track
        this.currentPlaylist.items.forEach((item, index) => {
          item.isCurrent = index === trackIndex;
        });
        
        // Update player status
        this.playerStatus.currentSong = this.currentPlaylist.items[trackIndex];
        this.playerStatus.position = 0;
        this.playerStatus.state = PlayerState.PLAYING;
        
        // Emit events
        this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
        this.emit(EventType.POSITION_CHANGE, this.playerStatus.position);
        this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
      }
      
      return Promise.resolve();
    }
  }

  // Export public API
  return {
    AmoraClient,
    PlayerState,
    ConnectionStatus,
    EventType
  };
})();
