#!/bin/bash

# This script sets up the EC2 instance for deployment

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
# First try to install the Docker Compose plugin (newer approach)
echo "Installing Docker Compose..."
if sudo apt-get install -y docker-compose-plugin; then
    echo "Docker Compose plugin installed successfully."
    # Test if it works
    if docker compose version; then
        echo "Using Docker Compose plugin"
    else
        # Fall back to standalone install if plugin doesn't work properly
        echo "Plugin installed but not working, falling back to standalone install..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "Standalone Docker Compose installed successfully."
    fi
else
    # Fallback to the standalone binary if plugin installation fails
    echo "Plugin installation failed, installing standalone Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Standalone Docker Compose installed successfully."
fi

# Add current user to docker group
sudo usermod -aG docker $USER

# Create app directory
mkdir -p ~/csc648-fa25-0104-team02

echo "EC2 instance is ready for deployment!"
echo "Important: Log out and log back in for docker group changes to take effect."
