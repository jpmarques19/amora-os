/**
 * Tests for the Amora Client SDK
 */

import { AmoraClient, EventType, PlayerState, ConnectionStatus } from './index';

// Mock the MQTT client
jest.mock('mqtt', () => {
  const EventEmitter = require('events');
  
  class MockMQTTClient extends EventEmitter {
    connect = jest.fn().mockReturnValue(this);
    subscribe = jest.fn().mockImplementation((topic, options, callback) => {
      if (callback) callback(null);
      return this;
    });
    publish = jest.fn().mockImplementation((topic, payload, options, callback) => {
      if (callback) callback(null);
      return this;
    });
    end = jest.fn().mockImplementation((force, callback) => {
      if (callback) callback();
      return this;
    });
  }
  
  return {
    connect: jest.fn().mockImplementation(() => {
      const client = new MockMQTTClient();
      setTimeout(() => {
        client.emit('connect');
      }, 10);
      return client;
    })
  };
});

describe('AmoraClient', () => {
  let client: AmoraClient;
  
  beforeEach(() => {
    client = new AmoraClient({
      brokerUrl: 'localhost',
      port: 1883,
      deviceId: 'test-device'
    });
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  describe('Connection', () => {
    it('should connect to the MQTT broker', async () => {
      const connectPromise = client.connect();
      
      // Wait for the connection to complete
      await connectPromise;
      
      expect(client.getConnectionStatus()).toBe(ConnectionStatus.CONNECTED);
    });
    
    it('should disconnect from the MQTT broker', async () => {
      // Connect first
      await client.connect();
      
      // Then disconnect
      await client.disconnect();
      
      expect(client.getConnectionStatus()).toBe(ConnectionStatus.DISCONNECTED);
    });
  });
  
  describe('Event handling', () => {
    it('should emit events when state changes', async () => {
      // Connect first
      await client.connect();
      
      // Set up event listener
      const stateChangeHandler = jest.fn();
      client.on(EventType.STATE_CHANGE, stateChangeHandler);
      
      // Simulate a state message
      const stateMessage = {
        state: PlayerState.PLAYING,
        currentSong: {
          title: 'Test Song',
          artist: 'Test Artist',
          album: 'Test Album',
          duration: 180,
          file: 'test.mp3'
        },
        volume: 80,
        repeat: false,
        random: false,
        timestamp: Date.now()
      };
      
      // Get the MQTT client instance
      const mqttClient = (client as any).mqttClient.client;
      
      // Simulate receiving a message on the state topic
      mqttClient.emit('message', 'amora/devices/test-device/state', Buffer.from(JSON.stringify(stateMessage)));
      
      // Check that the event was emitted
      expect(stateChangeHandler).toHaveBeenCalledWith(PlayerState.PLAYING);
      
      // Check that the player status was updated
      const status = client.getPlayerStatus();
      expect(status.state).toBe(PlayerState.PLAYING);
      expect(status.currentSong?.title).toBe('Test Song');
      expect(status.volume).toBe(80);
    });
  });
  
  describe('Player controls', () => {
    beforeEach(async () => {
      // Connect first
      await client.connect();
    });
    
    it('should send play command', async () => {
      // Set up a mock response
      const mqttClient = (client as any).mqttClient.client;
      
      // Create a promise that resolves when the command is sent
      const commandPromise = client.play();
      
      // Get the command ID from the pending commands
      const pendingCommands = (client as any).pendingCommands;
      const commandId = Array.from(pendingCommands.keys())[0];
      
      // Simulate a response
      const responseMessage = {
        commandId,
        result: true,
        message: 'Play command executed',
        timestamp: Date.now()
      };
      
      // Emit the response message
      mqttClient.emit('message', 'amora/devices/test-device/responses', Buffer.from(JSON.stringify(responseMessage)));
      
      // Wait for the command to complete
      await commandPromise;
      
      // Check that the command was sent
      expect(mqttClient.publish).toHaveBeenCalled();
      
      // Check that the command was removed from pending commands
      expect(pendingCommands.size).toBe(0);
    });
    
    it('should handle command errors', async () => {
      // Set up a mock response
      const mqttClient = (client as any).mqttClient.client;
      
      // Create a promise that should reject
      const commandPromise = client.play();
      
      // Get the command ID from the pending commands
      const pendingCommands = (client as any).pendingCommands;
      const commandId = Array.from(pendingCommands.keys())[0];
      
      // Simulate an error response
      const responseMessage = {
        commandId,
        result: false,
        message: 'Failed to play',
        timestamp: Date.now()
      };
      
      // Emit the response message
      mqttClient.emit('message', 'amora/devices/test-device/responses', Buffer.from(JSON.stringify(responseMessage)));
      
      // Wait for the command to fail
      await expect(commandPromise).rejects.toThrow('Failed to play');
      
      // Check that the command was removed from pending commands
      expect(pendingCommands.size).toBe(0);
    });
  });
  
  describe('Playlist management', () => {
    beforeEach(async () => {
      // Connect first
      await client.connect();
    });
    
    it('should fetch playlists', async () => {
      // Set up a mock response
      const mqttClient = (client as any).mqttClient.client;
      
      // Create a promise that resolves when the command is sent
      const commandPromise = client.getPlaylists();
      
      // Get the command ID from the pending commands
      const pendingCommands = (client as any).pendingCommands;
      const commandId = Array.from(pendingCommands.keys())[0];
      
      // Simulate a response with playlists
      const responseMessage = {
        commandId,
        result: true,
        message: 'Playlists retrieved',
        data: {
          result: [
            {
              name: 'Playlist 1',
              items: [
                {
                  title: 'Song 1',
                  artist: 'Artist 1',
                  album: 'Album 1',
                  duration: 180,
                  file: 'song1.mp3',
                  position: 0,
                  isCurrent: true
                }
              ]
            }
          ]
        },
        timestamp: Date.now()
      };
      
      // Emit the response message
      mqttClient.emit('message', 'amora/devices/test-device/responses', Buffer.from(JSON.stringify(responseMessage)));
      
      // Wait for the command to complete
      const playlists = await commandPromise;
      
      // Check that the playlists were returned
      expect(playlists).toHaveLength(1);
      expect(playlists[0].name).toBe('Playlist 1');
      expect(playlists[0].items).toHaveLength(1);
      expect(playlists[0].items[0].title).toBe('Song 1');
      
      // Check that the playlists were stored
      expect(client.getPlaylists()).toEqual(playlists);
    });
  });
});
