/**
 * Amora Client SDK
 * 
 * A TypeScript/JavaScript SDK for controlling Amora music player devices through MQTT.
 */

// Export main client class
export { AmoraClient } from './amora-client';

// Export types and interfaces
export {
  AmoraClientConfig,
  ConnectionOptions,
  QoS,
  PlayerState,
  SongMetadata,
  PlayerStatus,
  PlaylistItem,
  Playlist,
  CommandMessage,
  ResponseMessage,
  StateMessage,
  ConnectionStatus,
  EventType,
  EventListener,
  TopicType
} from './types';

// Export utility functions
export { createCommandMessage, parseMessage, createStateMessage } from './messages';

// Export MQTT client and topic manager (for advanced usage)
export { MQTTClient } from './mqtt-client';
export { TopicManager } from './topic-manager';
