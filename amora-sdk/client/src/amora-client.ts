/**
 * Main client class for the Amora Client SDK
 */

import { EventEmitter } from 'events';
import { MQTTClient } from './mqtt-client';
import { TopicManager } from './topic-manager';
import { createCommandMessage, parseMessage } from './messages';
import {
  AmoraClientConfig,
  QoS,
  PlayerStatus,
  Playlist,
  EventType,
  EventListener,
  TopicType,
  ConnectionStatus,
  CommandMessage,
  ResponseMessage,
  StateMessage,
  PlayerState
} from './types';

/**
 * Main client class for the Amora Client SDK
 */
export class AmoraClient extends EventEmitter {
  private mqttClient: MQTTClient;
  private topicManager: TopicManager;
  private config: AmoraClientConfig;
  private pendingCommands: Map<string, { resolve: Function; reject: Function; timestamp: number }> = new Map();
  private commandTimeout = 10000; // 10 seconds
  private commandTimeoutTimer: NodeJS.Timeout | null = null;
  private playerStatus: PlayerStatus = {
    state: PlayerState.STOPPED,
    volume: 0,
    repeat: false,
    random: false
  };
  private playlists: Playlist[] = [];

  /**
   * Create a new Amora client
   * @param config Client configuration
   */
  constructor(config: AmoraClientConfig) {
    super();
    this.config = {
      ...config,
      clientId: config.clientId || `amora-client-${Date.now()}`,
      topicPrefix: config.topicPrefix || 'amora/devices',
      defaultQoS: config.defaultQoS || QoS.AT_LEAST_ONCE
    };
    this.mqttClient = new MQTTClient(this.config);
    this.topicManager = new TopicManager(this.config.topicPrefix!, this.config.deviceId);

    // Set up event handlers
    this.mqttClient.on('message', this.handleMessage.bind(this));
    this.mqttClient.on('connectionChange', this.handleConnectionChange.bind(this));
    this.mqttClient.on('error', (error) => this.emit(EventType.ERROR, error));

    // Start command timeout checker
    this.startCommandTimeoutChecker();
  }

  /**
   * Connect to the MQTT broker
   * @returns Promise that resolves when connected
   */
  public async connect(): Promise<void> {
    try {
      await this.mqttClient.connect();
      
      // Subscribe to topics
      for (const topic of this.topicManager.getSubscriptionTopics()) {
        await this.mqttClient.subscribe(topic);
      }
      
      // Get initial status
      await this.getStatus();
    } catch (error) {
      this.emit(EventType.ERROR, error);
      throw error;
    }
  }

  /**
   * Disconnect from the MQTT broker
   */
  public async disconnect(): Promise<void> {
    try {
      // Stop command timeout checker
      if (this.commandTimeoutTimer) {
        clearInterval(this.commandTimeoutTimer);
        this.commandTimeoutTimer = null;
      }
      
      // Reject all pending commands
      for (const [commandId, { reject }] of this.pendingCommands.entries()) {
        reject(new Error('Client disconnected'));
        this.pendingCommands.delete(commandId);
      }
      
      await this.mqttClient.disconnect();
    } catch (error) {
      this.emit(EventType.ERROR, error);
      throw error;
    }
  }

  /**
   * Get the current connection status
   */
  public getConnectionStatus(): ConnectionStatus {
    return this.mqttClient.getConnectionStatus();
  }

  /**
   * Get the current player status
   */
  public getPlayerStatus(): PlayerStatus {
    return { ...this.playerStatus };
  }

  /**
   * Get the available playlists
   */
  public getPlaylists(): Playlist[] {
    return [...this.playlists];
  }

  /**
   * Register an event listener
   * @param event Event type
   * @param listener Event listener
   */
  public on(event: EventType, listener: EventListener): this {
    return super.on(event, listener);
  }

  /**
   * Remove an event listener
   * @param event Event type
   * @param listener Event listener
   */
  public off(event: EventType, listener: EventListener): this {
    return super.off(event, listener);
  }

  /**
   * Send a command to the player
   * @param command Command name
   * @param params Command parameters
   * @returns Promise that resolves with the command response
   */
  private async sendCommand(command: string, params?: any): Promise<ResponseMessage> {
    const commandMessage = createCommandMessage(command, params);
    const topic = this.topicManager.getTopic(TopicType.COMMANDS);

    return new Promise((resolve, reject) => {
      // Add to pending commands
      this.pendingCommands.set(commandMessage.commandId, {
        resolve,
        reject,
        timestamp: Date.now()
      });

      // Send command
      this.mqttClient.publish(topic, commandMessage)
        .catch((error) => {
          this.pendingCommands.delete(commandMessage.commandId);
          reject(error);
        });
    });
  }

  /**
   * Handle an incoming message
   * @param topic Message topic
   * @param payload Message payload
   */
  private handleMessage(topic: string, payload: Buffer): void {
    const topicType = this.topicManager.parseTopic(topic);
    if (!topicType) {
      return;
    }

    const message = parseMessage(payload);
    if (!message) {
      return;
    }

    switch (topicType) {
      case TopicType.STATE:
        this.handleStateMessage(message as StateMessage);
        break;
      case TopicType.RESPONSES:
        this.handleResponseMessage(message as ResponseMessage);
        break;
    }
  }

  /**
   * Handle a state message
   * @param message State message
   */
  private handleStateMessage(message: StateMessage): void {
    const oldStatus = { ...this.playerStatus };
    
    // Update player status
    this.playerStatus = {
      state: message.state,
      currentSong: message.currentSong,
      volume: message.volume,
      repeat: message.repeat,
      random: message.random
    };
    
    // Emit events for changes
    if (oldStatus.state !== this.playerStatus.state) {
      this.emit(EventType.STATE_CHANGE, this.playerStatus.state);
    }
    
    if (oldStatus.currentSong?.position !== this.playerStatus.currentSong?.position) {
      this.emit(EventType.POSITION_CHANGE, this.playerStatus.currentSong?.position);
    }
    
    if (oldStatus.volume !== this.playerStatus.volume) {
      this.emit(EventType.VOLUME_CHANGE, this.playerStatus.volume);
    }
  }

  /**
   * Handle a response message
   * @param message Response message
   */
  private handleResponseMessage(message: ResponseMessage): void {
    // Check if this is a response to a pending command
    const pendingCommand = this.pendingCommands.get(message.commandId);
    if (pendingCommand) {
      // Remove from pending commands
      this.pendingCommands.delete(message.commandId);
      
      // Resolve or reject the promise
      if (message.result) {
        pendingCommand.resolve(message);
      } else {
        pendingCommand.reject(new Error(message.message || 'Command failed'));
      }
    }
    
    // Emit event
    this.emit(EventType.COMMAND_RESPONSE, message);
    
    // Handle specific responses
    if (message.data) {
      if (message.data.playlists) {
        this.playlists = message.data.playlists;
        this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
      }
    }
  }

  /**
   * Handle a connection change
   * @param status New connection status
   */
  private handleConnectionChange(status: ConnectionStatus): void {
    this.emit(EventType.CONNECTION_CHANGE, status);
  }

  /**
   * Start the command timeout checker
   */
  private startCommandTimeoutChecker(): void {
    this.commandTimeoutTimer = setInterval(() => {
      const now = Date.now();
      
      for (const [commandId, { reject, timestamp }] of this.pendingCommands.entries()) {
        if (now - timestamp > this.commandTimeout) {
          reject(new Error('Command timed out'));
          this.pendingCommands.delete(commandId);
        }
      }
    }, 1000);
  }

  // Player control methods

  /**
   * Start playback
   */
  public async play(): Promise<void> {
    await this.sendCommand('play');
  }

  /**
   * Pause playback
   */
  public async pause(): Promise<void> {
    await this.sendCommand('pause');
  }

  /**
   * Stop playback
   */
  public async stop(): Promise<void> {
    await this.sendCommand('stop');
  }

  /**
   * Skip to the next track
   */
  public async next(): Promise<void> {
    await this.sendCommand('next');
  }

  /**
   * Go back to the previous track
   */
  public async previous(): Promise<void> {
    await this.sendCommand('previous');
  }

  /**
   * Set the volume
   * @param volume Volume level (0-100)
   */
  public async setVolume(volume: number): Promise<void> {
    await this.sendCommand('set_volume', { volume });
  }

  /**
   * Get the current volume
   */
  public async getVolume(): Promise<number> {
    const response = await this.sendCommand('get_volume');
    return response.data.result;
  }

  /**
   * Set repeat mode
   * @param repeat Whether to enable repeat mode
   */
  public async setRepeat(repeat: boolean): Promise<void> {
    await this.sendCommand('set_repeat', { repeat });
  }

  /**
   * Set random mode
   * @param random Whether to enable random mode
   */
  public async setRandom(random: boolean): Promise<void> {
    await this.sendCommand('set_random', { random });
  }

  /**
   * Get the current player status
   */
  public async getStatus(): Promise<PlayerStatus> {
    const response = await this.sendCommand('get_status');
    return response.data.result;
  }

  /**
   * Get the available playlists
   */
  public async getPlaylists(): Promise<Playlist[]> {
    const response = await this.sendCommand('get_playlists');
    this.playlists = response.data.result;
    this.emit(EventType.PLAYLIST_CHANGE, this.playlists);
    return this.playlists;
  }

  /**
   * Play a playlist
   * @param playlist Playlist name
   */
  public async playPlaylist(playlist: string): Promise<void> {
    await this.sendCommand('play_playlist', { playlist });
  }

  /**
   * Get songs in a playlist
   * @param playlist Playlist name
   */
  public async getPlaylistSongs(playlist: string): Promise<SongMetadata[]> {
    const response = await this.sendCommand('get_playlist_songs', { playlist });
    return response.data.result;
  }

  /**
   * Create a playlist
   * @param name Playlist name
   * @param files List of files to add to the playlist
   */
  public async createPlaylist(name: string, files: string[]): Promise<void> {
    await this.sendCommand('create_playlist', { name, files });
  }

  /**
   * Delete a playlist
   * @param playlist Playlist name
   */
  public async deletePlaylist(playlist: string): Promise<void> {
    await this.sendCommand('delete_playlist', { playlist });
  }

  /**
   * Update the music database
   */
  public async updateDatabase(): Promise<void> {
    await this.sendCommand('update_database');
  }

  /**
   * Play a specific track by index
   * @param trackIndex Track index in the current playlist
   */
  public async playTrack(trackIndex: number): Promise<void> {
    await this.sendCommand('play_track', { trackIndex });
  }

  /**
   * Add a track to a playlist
   * @param track Track to add
   * @param playlist Playlist to add to
   */
  public async addTrack(track: string, playlist: string): Promise<void> {
    await this.sendCommand('add_track', { track, playlist });
  }

  /**
   * Remove a track from a playlist
   * @param trackIndex Track index in the playlist
   * @param playlist Playlist to remove from
   */
  public async removeTrack(trackIndex: number, playlist: string): Promise<void> {
    await this.sendCommand('remove_track', { trackIndex, playlist });
  }

  /**
   * Reorder tracks in a playlist
   * @param fromIndex Original position
   * @param toIndex New position
   * @param playlist Playlist to reorder
   */
  public async reorderTrack(fromIndex: number, toIndex: number, playlist: string): Promise<void> {
    await this.sendCommand('reorder_track', { fromIndex, toIndex, playlist });
  }
}
