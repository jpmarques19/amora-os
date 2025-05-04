FROM debian:bookworm

# Install dependencies
RUN apt-get update && apt-get install -y \
    mpd \
    mpc \
    alsa-utils \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    python3-dev \
    curl \
    socat \
    nano \
    wget \
    sudo \
    net-tools \
    iputils-ping \
    procps \
    dbus \
    pulseaudio \
    pulseaudio-utils \
    psmisc \
    lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure PulseAudio for network access (for dev mode)
RUN mkdir -p /etc/pulse
COPY config/pulse-client.conf /etc/pulse/client.conf
COPY config/pulse-system.pa /etc/pulse/system.pa

# Create user
RUN useradd -m -s /bin/bash user && \
    echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/user

# Set up directories
RUN mkdir -p /home/user/music/playlists \
    /home/user/app \
    /home/user/.config/mpd \
    /home/user/.local/share/mpd \
    /home/user/logs

# Set permissions
RUN chown -R user:user /home/user

# Switch to user
USER user
WORKDIR /home/user/app

# Create a virtual environment
RUN python3 -m venv /home/user/venv
ENV PATH="/home/user/venv/bin:$PATH"
ENV VIRTUAL_ENV="/home/user/venv"

# Copy pyproject.toml and poetry.lock
COPY --chown=user:user pyproject.toml poetry.lock* /home/user/app/

# Install dependencies with pip in the virtual environment
RUN pip install --upgrade pip && \
    pip install click python-mpd2 asyncio pydantic

# Copy application files
COPY --chown=user:user src /home/user/app/src
COPY --chown=user:user config /home/user/app/config
COPY --chown=user:user scripts /home/user/app/scripts

# Make scripts executable
RUN chmod +x /home/user/app/scripts/*.sh
RUN chmod +x /home/user/app/scripts/*.py

# Set up Pipewire
RUN mkdir -p /home/user/.config/systemd/user
RUN mkdir -p /home/user/.config/pipewire

# Create start script
USER root
RUN echo '#!/bin/bash\n\
# Create necessary directories\n\
mkdir -p /home/user/music/playlists\n\
mkdir -p /home/user/.config/mpd\n\
mkdir -p /home/user/.local/share/mpd\n\
mkdir -p /home/user/logs\n\
\n\
# Copy MPD configuration\n\
cp /home/user/app/config/mpd.conf /home/user/.config/mpd/mpd.conf\n\
\n\
# In dev mode, we need to use PulseAudio to pipe audio to Windows host\n\
echo "Starting audio services..."\n\
\n\
# Kill any existing PulseAudio processes\n\
killall -9 pulseaudio 2>/dev/null || true\n\
\n\
# Configure PulseAudio to connect to the Windows host\n\
sudo mkdir -p /home/user/.config/pulse\n\
echo "default-server = host.docker.internal" > /home/user/.config/pulse/client.conf\n\
echo "autospawn = no" >> /home/user/.config/pulse/client.conf\n\
export PULSE_SERVER=host.docker.internal\n\
\n\
# Start PulseAudio client\n\
pulseaudio -D --exit-idle-time=-1\n\
sleep 2\n\
\n\
# Start MPD with the correct configuration\n\
echo "Starting MPD..."\n\
mpd /home/user/.config/mpd/mpd.conf\n\
sleep 3\n\
\n\
# Verify MPD is running\n\
echo "Checking if MPD is running..."\n\
mpc status\n\
if [ $? -ne 0 ]; then\n\
  echo "MPD failed to start properly. Checking logs:"\n\
  cat /var/log/mpd/mpd.log 2>/dev/null || echo "No MPD log found"\n\
  # Try to restart MPD\n\
  echo "Trying to restart MPD..."\n\
  mpd --kill\n\
  sleep 1\n\
  mpd /home/user/.config/mpd/mpd.conf\n\
  sleep 2\n\
  mpc status || echo "MPD still failed to start properly"\n\
fi\n\
\n\
# Set volume\n\
echo "Setting volume..."\n\
mpc volume 100\n\
\n\
# Fix permissions for music files\n\
echo "Fixing music file permissions..."\n\
sudo chmod -R 777 /home/user/music\n\
sudo chown -R user:user /home/user/music\n\
\n\
# Play a test sound to verify audio is working\n\
echo "Playing test sound..."\n\
mpc clear\n\
mpc update\n\
sleep 2\n\
mpc add "$(find /home/user/music -name "*.mp3" | head -n 1)"\n\
mpc play\n\
\n\
# Start the Python application with dev mode flag\n\
echo "Starting Python application in dev mode..."\n\
cd /home/user/app\n\
source /home/user/venv/bin/activate\n\
export PYTHONPATH=/home/user/app\n\
python -m src.main start --dev\n\
\n\
# Keep container running if the application exits\n\
tail -f /dev/null\n\
' > /home/user/start.sh

RUN chmod +x /home/user/start.sh
RUN chown user:user /home/user/start.sh

USER user
WORKDIR /home/user/app

CMD ["/home/user/start.sh"]
