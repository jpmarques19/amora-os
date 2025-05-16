/**
 * Basic usage example for the Amora Client SDK
 */

const { AmoraClient, EventType, PlayerState } = require('../dist');

// Create client configuration
const config = {
  brokerUrl: 'localhost',
  port: 1883,
  deviceId: 'amora-player-001',
  connectionOptions: {
    username: 'your_username',  // Optional
    password: 'your_password',  // Optional
    useTls: false,
    keepAlive: 60,
    cleanSession: true,
    reconnectOnFailure: true
  }
};

// Create client instance
const client = new AmoraClient(config);

// Set up event listeners
client.on(EventType.CONNECTION_CHANGE, (status) => {
  console.log(`Connection status changed: ${status}`);
});

client.on(EventType.STATE_CHANGE, (state) => {
  console.log(`Player state changed: ${state}`);
});

client.on(EventType.POSITION_CHANGE, (position) => {
  if (position !== undefined) {
    const minutes = Math.floor(position / 60);
    const seconds = Math.floor(position % 60);
    console.log(`Position changed: ${minutes}:${seconds.toString().padStart(2, '0')}`);
  }
});

client.on(EventType.VOLUME_CHANGE, (volume) => {
  console.log(`Volume changed: ${volume}%`);
});

client.on(EventType.PLAYLIST_CHANGE, (playlists) => {
  console.log(`Playlists updated: ${playlists.length} playlists available`);
});

client.on(EventType.ERROR, (error) => {
  console.error(`Error: ${error.message}`);
});

// Connect to the MQTT broker
async function run() {
  try {
    console.log('Connecting to MQTT broker...');
    await client.connect();
    console.log('Connected!');

    // Get current status
    const status = await client.getStatus();
    console.log('Current status:', status);

    // Get available playlists
    const playlists = await client.getPlaylists();
    console.log(`Available playlists: ${playlists.map(p => p.name).join(', ')}`);

    // Control the player
    console.log('Playing...');
    await client.play();

    // Wait for 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('Pausing...');
    await client.pause();

    // Wait for 2 seconds
    await new Promise(resolve => setTimeout(resolve, 2000));

    console.log('Setting volume to 80%...');
    await client.setVolume(80);

    // Wait for 2 seconds
    await new Promise(resolve => setTimeout(resolve, 2000));

    console.log('Playing next track...');
    await client.next();

    // Wait for 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('Stopping...');
    await client.stop();

    // Disconnect when done
    console.log('Disconnecting...');
    await client.disconnect();
    console.log('Disconnected!');
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the example
run();
