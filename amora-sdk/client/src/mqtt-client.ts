/**
 * MQTT client wrapper for the Amora Client SDK
 */

import * as mqtt from 'mqtt';
import { EventEmitter } from 'events';
import { AmoraClientConfig, ConnectionOptions, QoS, ConnectionStatus } from './types';

/**
 * MQTT client wrapper for the Amora Client SDK
 */
export class MQTTClient extends EventEmitter {
  private client: mqtt.MqttClient | null = null;
  private config: AmoraClientConfig;
  private connectionStatus: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectDelay = 1000; // Initial reconnect delay in ms

  /**
   * Create a new MQTT client
   * @param config Client configuration
   */
  constructor(config: AmoraClientConfig) {
    super();
    this.config = {
      ...config,
      clientId: config.clientId || `amora-client-${Date.now()}`,
      topicPrefix: config.topicPrefix || 'amora/devices',
      defaultQoS: config.defaultQoS || QoS.AT_LEAST_ONCE,
      connectionOptions: {
        keepAlive: 60,
        cleanSession: true,
        reconnectOnFailure: true,
        maxReconnectDelay: 300,
        ...config.connectionOptions
      }
    };
  }

  /**
   * Get the connection status
   */
  public getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  /**
   * Connect to the MQTT broker
   * @returns Promise that resolves when connected
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.client && this.connectionStatus === ConnectionStatus.CONNECTED) {
        resolve();
        return;
      }

      this.setConnectionStatus(ConnectionStatus.CONNECTING);

      // Build connection options
      const options: mqtt.IClientOptions = {
        clientId: this.config.clientId,
        keepalive: this.config.connectionOptions?.keepAlive || 60,
        clean: this.config.connectionOptions?.cleanSession !== false,
        reconnectPeriod: this.config.connectionOptions?.reconnectOnFailure === false ? 0 : 1000,
        username: this.config.connectionOptions?.username,
        password: this.config.connectionOptions?.password,
        protocol: this.config.connectionOptions?.useTls ? 'mqtts' : 'mqtt'
      };

      // Add TLS options if needed
      if (this.config.connectionOptions?.useTls) {
        options.rejectUnauthorized = true;
        
        if (this.config.connectionOptions.caCertPath) {
          options.ca = [this.config.connectionOptions.caCertPath];
        }
        
        if (this.config.connectionOptions.clientCertPath && this.config.connectionOptions.clientKeyPath) {
          options.cert = this.config.connectionOptions.clientCertPath;
          options.key = this.config.connectionOptions.clientKeyPath;
        }
      }

      // Create MQTT client
      const url = `${this.config.connectionOptions?.useTls ? 'mqtts' : 'mqtt'}://${this.config.brokerUrl}:${this.config.port}`;
      this.client = mqtt.connect(url, options);

      // Set up event handlers
      this.client.on('connect', () => {
        this.setConnectionStatus(ConnectionStatus.CONNECTED);
        this.reconnectDelay = 1000; // Reset reconnect delay
        resolve();
      });

      this.client.on('error', (error) => {
        this.emit('error', error);
        if (this.connectionStatus === ConnectionStatus.CONNECTING) {
          reject(error);
        }
      });

      this.client.on('offline', () => {
        this.setConnectionStatus(ConnectionStatus.DISCONNECTED);
      });

      this.client.on('reconnect', () => {
        this.setConnectionStatus(ConnectionStatus.CONNECTING);
      });

      this.client.on('message', (topic, payload) => {
        this.emit('message', topic, payload);
      });

      this.client.on('close', () => {
        this.setConnectionStatus(ConnectionStatus.DISCONNECTED);
        
        // If reconnect is disabled, try to reconnect manually
        if (this.config.connectionOptions?.reconnectOnFailure !== false && 
            options.reconnectPeriod === 0) {
          this.scheduleReconnect();
        }
      });
    });
  }

  /**
   * Disconnect from the MQTT broker
   */
  public disconnect(): Promise<void> {
    return new Promise((resolve) => {
      if (!this.client || this.connectionStatus === ConnectionStatus.DISCONNECTED) {
        resolve();
        return;
      }

      // Clear reconnect timer
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      this.client.end(false, () => {
        this.setConnectionStatus(ConnectionStatus.DISCONNECTED);
        resolve();
      });
    });
  }

  /**
   * Subscribe to a topic
   * @param topic Topic to subscribe to
   * @param qos QoS level
   */
  public subscribe(topic: string, qos: QoS = this.config.defaultQoS || QoS.AT_LEAST_ONCE): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.client || this.connectionStatus !== ConnectionStatus.CONNECTED) {
        reject(new Error('Not connected to MQTT broker'));
        return;
      }

      this.client.subscribe(topic, { qos }, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Unsubscribe from a topic
   * @param topic Topic to unsubscribe from
   */
  public unsubscribe(topic: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.client || this.connectionStatus !== ConnectionStatus.CONNECTED) {
        reject(new Error('Not connected to MQTT broker'));
        return;
      }

      this.client.unsubscribe(topic, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Publish a message to a topic
   * @param topic Topic to publish to
   * @param payload Message payload
   * @param qos QoS level
   * @param retain Whether to retain the message
   */
  public publish(
    topic: string, 
    payload: string | Buffer | object, 
    qos: QoS = this.config.defaultQoS || QoS.AT_LEAST_ONCE, 
    retain = false
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.client || this.connectionStatus !== ConnectionStatus.CONNECTED) {
        reject(new Error('Not connected to MQTT broker'));
        return;
      }

      // Convert object to JSON string
      let messagePayload = payload;
      if (typeof payload === 'object' && !(payload instanceof Buffer)) {
        messagePayload = JSON.stringify(payload);
      }

      this.client.publish(topic, messagePayload as string | Buffer, { qos, retain }, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Set the connection status and emit an event
   * @param status New connection status
   */
  private setConnectionStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      this.emit('connectionChange', status);
    }
  }

  /**
   * Schedule a reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(() => {
        // Increase reconnect delay with exponential backoff, up to max
        const maxDelay = (this.config.connectionOptions?.maxReconnectDelay || 300) * 1000;
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, maxDelay);
        this.scheduleReconnect();
      });
    }, this.reconnectDelay);
  }
}
