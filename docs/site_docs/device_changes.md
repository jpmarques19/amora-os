# Device-Side Changes for AmoraSDK Integration

## Overview

To integrate the AmoraSDK with the existing AmoraOS device, several changes are needed. This document outlines these changes and provides implementation guidance.

## Required Changes

### 1. Install Additional Dependencies

The AmoraSDK server requires additional Python packages that need to be installed on the device:

```bash
# Using Poetry
poetry add fastapi uvicorn websockets

# Or using pip in the container
pip install fastapi uvicorn websockets
```

These dependencies should be added to:
- `edge/pyproject.toml` (for Poetry)
- `edge/Dockerfile` (for container deployment)

### 2. Update Network Configuration

The device needs to expose the SDK server ports to the network:

- HTTP API: Port 8000 (default)
- WebSocket: Same port as HTTP API

For Docker deployment, update the `docker run` command to expose these ports:

```bash
docker run -d --name waybox-player-python --privileged --network host \
  -v ./music:/home/user/music \
  -p 8000:8000 \  # Add this line
  --device /dev/snd:/dev/snd \
  --group-add audio \
  waybox-python-player
```

### 3. SDK Server Integration

There are two approaches to integrate the SDK server with the existing application:

#### Option A: Standalone Process (Recommended for Initial Development)

1. Create a startup script for the SDK server:

```bash
# File: edge/scripts/start-sdk-server.sh
#!/bin/bash
cd /home/user/app
source /home/user/venv/bin/activate
export PYTHONPATH=/home/user/app:/home/user/sdk
python -m amora_sdk.server
```

2. Update the container startup to launch both the main application and the SDK server:

```bash
# Update edge/scripts/start.sh to launch the SDK server
# Add at the end of the file:
echo "Starting SDK server..."
/home/user/app/scripts/start-sdk-server.sh &
```

#### Option B: Integrated Component (Recommended for Production)

1. Modify the main application to initialize and start the SDK server:

```python
# Add to edge/src/main.py

from amora_sdk import AmoraServer

async def run_player(config):
    # ... existing code ...
    
    # Initialize music player
    player = MusicPlayer(config.audio.model_dump())
    
    # Initialize SDK server
    sdk_server = AmoraServer(config.audio.model_dump(), host="0.0.0.0", port=8000)
    sdk_server.start()
    
    # ... rest of existing code ...
    
    try:
        # ... existing code ...
    finally:
        # ... existing code ...
        sdk_server.stop()
```

### 4. Update Dockerfile

Update the Dockerfile to include the SDK files:

```dockerfile
# Add to edge/Dockerfile

# Copy SDK files
COPY --chown=user:user sdk/amora_sdk /home/user/sdk/amora_sdk
```

### 5. Configure CORS (Cross-Origin Resource Sharing)

To allow web applications from different origins to access the API, CORS needs to be properly configured:

```python
# This is already included in the AmoraServer implementation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Implementation Steps

Here's a step-by-step guide to implementing these changes:

### 1. Install SDK Dependencies

```bash
cd edge
poetry add fastapi uvicorn websockets
```

### 2. Copy SDK Files to Device

```bash
# If using Docker
docker cp sdk/amora_sdk waybox-player-python:/home/user/sdk/

# If using direct deployment
cp -r sdk/amora_sdk /path/to/device/sdk/
```

### 3. Create SDK Server Startup Script

```bash
# Create the script
cat > edge/scripts/start-sdk-server.sh << 'EOF'
#!/bin/bash
cd /home/user/app
source /home/user/venv/bin/activate
export PYTHONPATH=/home/user/app:/home/user/sdk
python -m amora_sdk.server
EOF

# Make it executable
chmod +x edge/scripts/start-sdk-server.sh
```

### 4. Update Main Startup Script

```bash
# Edit edge/scripts/start.sh to add SDK server startup
echo "Starting SDK server..."
/home/user/app/scripts/start-sdk-server.sh &
```

### 5. Rebuild and Restart Container

```bash
# Rebuild container
docker build -t waybox-python-player .

# Stop existing container
docker stop waybox-player-python
docker rm waybox-player-python

# Start new container with port mapping
docker run -d --name waybox-player-python --privileged --network host \
  -v ./music:/home/user/music \
  -p 8000:8000 \
  --device /dev/snd:/dev/snd \
  --group-add audio \
  waybox-python-player
```

## Testing the Integration

After implementing these changes, you can test the integration:

1. Check if the SDK server is running:

```bash
curl http://device-ip:8000/api/status
```

2. Test the WebSocket connection:

```bash
# Using websocat tool
websocat ws://device-ip:8000/ws
```

3. Run the test application:

```bash
cd sdk/test_app
npm install
npm start
```

Then open a browser to http://localhost:3000 and connect to the device using its IP address.

## Troubleshooting

### Server Not Starting

Check the logs for errors:

```bash
docker logs waybox-player-python
```

### Connection Issues

Ensure the ports are properly exposed:

```bash
# Check if the server is listening on port 8000
docker exec waybox-player-python netstat -tuln | grep 8000
```

### CORS Issues

If web applications cannot connect, check for CORS errors in the browser console and ensure the CORS middleware is properly configured.
