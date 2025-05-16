/**
 * Topic manager for the Amora Client SDK
 */

import { TopicType } from './types';

/**
 * Manages MQTT topics for the Amora Client SDK
 */
export class TopicManager {
  private topicPrefix: string;
  private deviceId: string;
  private validTopics: Set<string> = new Set();

  /**
   * Create a new topic manager
   * @param topicPrefix Prefix for all topics
   * @param deviceId Device ID
   */
  constructor(topicPrefix: string, deviceId: string) {
    this.topicPrefix = topicPrefix;
    this.deviceId = deviceId;
    this.initializeValidTopics();
  }

  /**
   * Initialize the set of valid topics
   */
  private initializeValidTopics(): void {
    Object.values(TopicType).forEach(topicType => {
      this.validTopics.add(this.getTopic(topicType));
    });
  }

  /**
   * Get the full topic string for a given topic type
   * @param topicType Type of the topic
   * @returns Full topic string
   */
  public getTopic(topicType: TopicType): string {
    return `${this.topicPrefix}/${this.deviceId}/${topicType}`;
  }

  /**
   * Check if a topic is valid
   * @param topic Topic to check
   * @returns True if the topic is valid, false otherwise
   */
  public isValidTopic(topic: string): boolean {
    return this.validTopics.has(topic);
  }

  /**
   * Parse a topic string and return its type
   * @param topic Topic string to parse
   * @returns TopicType if the topic is valid, undefined otherwise
   */
  public parseTopic(topic: string): TopicType | undefined {
    if (!this.isValidTopic(topic)) {
      return undefined;
    }

    // Extract the topic type from the topic string
    const parts = topic.split('/');
    if (parts.length < 3) {
      return undefined;
    }

    const topicTypeStr = parts[parts.length - 1];
    return Object.values(TopicType).find(t => t === topicTypeStr);
  }

  /**
   * Get the list of topics to subscribe to
   * @returns List of topics to subscribe to
   */
  public getSubscriptionTopics(): string[] {
    return [
      this.getTopic(TopicType.STATE),
      this.getTopic(TopicType.RESPONSES)
    ];
  }

  /**
   * Get a wildcard topic for the device
   * @returns Wildcard topic string
   */
  public getWildcardTopic(): string {
    return `${this.topicPrefix}/${this.deviceId}/#`;
  }
}
