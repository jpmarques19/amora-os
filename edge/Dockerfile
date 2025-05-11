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
    /home/user/music/samples \
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
    pip install click python-mpd2 asyncio pydantic azure-iot-device uvicorn fastapi

# Copy application files
COPY --chown=user:user src /home/user/app/src
COPY --chown=user:user config /home/user/app/config
COPY --chown=user:user scripts /home/user/app/scripts

# Copy sample music files
COPY --chown=user:user samples/*.mp3 /home/user/music/samples/

# Make scripts executable
RUN chmod +x /home/user/app/scripts/*.sh
RUN chmod +x /home/user/app/scripts/*.py

# Configure network settings for better IoT connectivity
USER root
RUN echo "net.ipv4.tcp_keepalive_time = 60" >> /etc/sysctl.conf && \
    echo "net.ipv4.tcp_keepalive_intvl = 10" >> /etc/sysctl.conf && \
    echo "net.ipv4.tcp_keepalive_probes = 6" >> /etc/sysctl.conf

# Set up Pipewire
RUN mkdir -p /home/user/.config/systemd/user
RUN mkdir -p /home/user/.config/pipewire

# Copy start script from scripts directory to home directory
USER root
COPY --chown=user:user scripts/start.sh /home/user/start.sh
RUN chmod +x /home/user/start.sh

USER user
WORKDIR /home/user/app

CMD ["/home/user/start.sh"]
