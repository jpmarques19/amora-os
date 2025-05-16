/**
 * Types and interfaces for the Amora Client SDK
 */

/**
 * Quality of Service level for MQTT messages
 */
export enum QoS {
  AT_MOST_ONCE = 0,
  AT_LEAST_ONCE = 1,
  EXACTLY_ONCE = 2
}

/**
 * Connection options for MQTT client
 */
export interface ConnectionOptions {
  /** Username for MQTT broker authentication */
  username?: string;
  /** Password for MQTT broker authentication */
  password?: string;
  /** Whether to use TLS for the connection */
  useTls?: boolean;
  /** Path to CA certificate file for TLS */
  caCertPath?: string;
  /** Path to client certificate file for TLS */
  clientCertPath?: string;
  /** Path to client key file for TLS */
  clientKeyPath?: string;
  /** Keep alive interval in seconds */
  keepAlive?: number;
  /** Whether to use a clean session */
  cleanSession?: boolean;
  /** Whether to reconnect automatically on connection failure */
  reconnectOnFailure?: boolean;
  /** Maximum reconnect delay in seconds */
  maxReconnectDelay?: number;
}

/**
 * Configuration for the Amora Client SDK
 */
export interface AmoraClientConfig {
  /** MQTT broker URL */
  brokerUrl: string;
  /** MQTT broker port */
  port: number;
  /** Client ID for MQTT connection */
  clientId?: string;
  /** Device ID to connect to */
  deviceId: string;
  /** Topic prefix for MQTT topics */
  topicPrefix?: string;
  /** Connection options for MQTT client */
  connectionOptions?: ConnectionOptions;
  /** Default QoS level for MQTT messages */
  defaultQoS?: QoS;
}

/**
 * Player state
 */
export enum PlayerState {
  PLAYING = 'playing',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  LOADING = 'loading',
  ERROR = 'error'
}

/**
 * Song metadata
 */
export interface SongMetadata {
  /** Song title */
  title: string;
  /** Artist name */
  artist: string;
  /** Album name */
  album: string;
  /** Album art URL */
  albumArt?: string;
  /** Song duration in seconds */
  duration: number;
  /** File path or URL */
  file: string;
  /** Additional metadata */
  [key: string]: any;
}

/**
 * Player status
 */
export interface PlayerStatus {
  /** Current player state */
  state: PlayerState;
  /** Current song metadata */
  currentSong?: SongMetadata;
  /** Current playback position in seconds */
  position?: number;
  /** Current volume (0-100) */
  volume: number;
  /** Whether repeat mode is enabled */
  repeat: boolean;
  /** Whether random mode is enabled */
  random: boolean;
}

/**
 * Playlist item
 */
export interface PlaylistItem extends SongMetadata {
  /** Position in the playlist */
  position: number;
  /** Whether this is the current song */
  isCurrent: boolean;
}

/**
 * Playlist
 */
export interface Playlist {
  /** Playlist name */
  name: string;
  /** Playlist items */
  items: PlaylistItem[];
}

/**
 * Command message
 */
export interface CommandMessage {
  /** Command name */
  command: string;
  /** Command ID */
  commandId: string;
  /** Command parameters */
  params?: any;
  /** Timestamp */
  timestamp: number;
}

/**
 * Response message
 */
export interface ResponseMessage {
  /** Command ID that this response is for */
  commandId: string;
  /** Whether the command was successful */
  result: boolean;
  /** Response message */
  message: string;
  /** Response data */
  data?: any;
  /** Timestamp */
  timestamp: number;
}

/**
 * State message
 */
export interface StateMessage {
  /** Player state */
  state: PlayerState;
  /** Current song */
  currentSong?: SongMetadata;
  /** Current position */
  position?: number;
  /** Current volume */
  volume: number;
  /** Whether repeat mode is enabled */
  repeat: boolean;
  /** Whether random mode is enabled */
  random: boolean;
  /** Timestamp */
  timestamp: number;
}

/**
 * Connection status
 */
export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  ERROR = 'error'
}

/**
 * Event types
 */
export enum EventType {
  STATE_CHANGE = 'stateChange',
  POSITION_CHANGE = 'positionChange',
  VOLUME_CHANGE = 'volumeChange',
  PLAYLIST_CHANGE = 'playlistChange',
  CONNECTION_CHANGE = 'connectionChange',
  COMMAND_RESPONSE = 'commandResponse',
  ERROR = 'error'
}

/**
 * Event listener
 */
export type EventListener = (data: any) => void;

/**
 * Topic type
 */
export enum TopicType {
  STATE = 'state',
  COMMANDS = 'commands',
  RESPONSES = 'responses',
  CONNECTION = 'connection'
}
