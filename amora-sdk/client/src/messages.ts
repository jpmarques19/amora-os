/**
 * Message handling utilities for the Amora Client SDK
 */

import { v4 as uuidv4 } from 'uuid';
import {
  CommandMessage,
  ResponseMessage,
  StateMessage,
  PlayerState,
  SongMetadata
} from './types';

/**
 * Create a command message
 * @param command Command name
 * @param params Command parameters
 * @returns Command message
 */
export function createCommandMessage(command: string, params?: any): CommandMessage {
  return {
    command,
    commandId: uuidv4(),
    params,
    timestamp: Date.now()
  };
}

/**
 * Parse a message payload
 * @param payload Message payload
 * @returns Parsed message or null if parsing failed
 */
export function parseMessage(payload: Buffer | string): CommandMessage | ResponseMessage | StateMessage | null {
  try {
    // Convert buffer to string if needed
    const payloadStr = payload instanceof Buffer ? payload.toString() : payload;

    // Parse JSON
    const data = JSON.parse(payloadStr);

    // Determine message type
    if ('command' in data && 'commandId' in data) {
      return data as CommandMessage;
    } else if ('result' in data && 'commandId' in data) {
      return data as ResponseMessage;
    } else if ('state' in data) {
      return data as StateMessage;
    }

    return null;
  } catch (error) {
    console.error('Error parsing message:', error);
    return null;
  }
}

/**
 * Create a state message from player status
 * @param state Player state
 * @param currentSong Current song
 * @param volume Current volume
 * @param repeat Whether repeat mode is enabled
 * @param random Whether random mode is enabled
 * @returns State message
 */
export function createStateMessage(
  state: PlayerState,
  currentSong?: SongMetadata,
  volume = 0,
  repeat = false,
  random = false
): StateMessage {
  return {
    state,
    currentSong,
    volume,
    repeat,
    random,
    timestamp: Date.now()
  };
}
