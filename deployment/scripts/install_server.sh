#!/bin/bash
set -e

echo "=== Ent_RAG Server Installation Script ==="
echo "=== Server: 185.193.17.27 | Domain: docintel.space ==="

# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y curl wget git ufw fail2ban htop unzip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose (v2 plugin)
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban for brute force protection
systemctl start fail2ban
systemctl enable fail2ban

# Create application directory
mkdir -p /opt/ent_rag
chown "$USER:$USER" /opt/ent_rag

echo "=== Server installation complete ==="
echo "=== Docker version: $(docker --version) ==="
echo "=== Docker Compose version: $(docker-compose --version) ==="
