#!/bin/bash
set -euo pipefail

# ==============================================================================
# n8n Automated Setup Script for Oracle Cloud Infrastructure (OCI)
# Installs Docker, configures OCI host firewalls (80/443), and starts n8n + Caddy
# ==============================================================================

echo "=========================================="
echo " Starting n8n Deployment on Oracle Cloud"
echo "=========================================="

# 1. Check Root / Sudo
if [ "$EUID" -ne 0 ]; then
  SUDO="sudo"
else
  SUDO=""
fi

# 2. Add Swapfile if RAM <= 2GB (Crucial for VM.Standard.E2.1.Micro instances)
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 2000 ]; then
  if ! swapon --show | grep -q "/swapfile"; then
    echo "⚠️ Low RAM detected (${TOTAL_RAM}MB). Creating 2GB swap space to keep n8n stable..."
    $SUDO fallocate -l 2G /swapfile || $SUDO dd if=/dev/zero of=/swapfile bs=1M count=2048
    $SUDO chmod 600 /swapfile
    $SUDO mkswap /swapfile
    $SUDO swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
      echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab
    fi
    echo "✅ 2GB swap space enabled."
  fi
fi

# 3. Check / Generate .env
if [ ! -f .env ]; then
  echo "Error: .env file not found. Creating from template..."
  cp .env.example .env 2>/dev/null || true
fi

# Ensure encryption key is uniquely generated if still default
if grep -q "CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY_12345" .env 2>/dev/null; then
  RANDOM_KEY=$(openssl rand -hex 24)
  sed -i "s/CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY_12345/${RANDOM_KEY}/g" .env
  echo " Generated fresh N8N_ENCRYPTION_KEY in .env"
fi

# 3. Install Docker & Docker Compose if missing
if ! command -v docker &> /dev/null; then
  echo " Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  $SUDO sh get-docker.sh
  rm -f get-docker.sh

  # Allow current user to run docker without sudo
  if [ -n "${SUDO_USER:-}" ]; then
    $SUDO usermod -aG docker "$SUDO_USER"
  elif [ -n "${USER:-}" ] && [ "$USER" != "root" ]; then
    $SUDO usermod -aG docker "$USER"
  fi

  $SUDO systemctl enable --now docker
  echo " Docker installed successfully."
fi

# 4. Oracle Cloud Host Firewall Configuration (CRITICAL FOR OCI)
echo " Configuring host firewall for ports 80 & 443..."
if command -v ufw &> /dev/null; then
  $SUDO ufw allow 80/tcp || true
  $SUDO ufw allow 443/tcp || true
  $SUDO ufw allow 443/udp || true
  $SUDO ufw allow 22/tcp || true
fi

if command -v iptables &> /dev/null; then
  # Oracle Cloud Ubuntu images include strict iptables rules by default (REJECT at line 5)
  $SUDO iptables -I INPUT 5 -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT 2>/dev/null || $SUDO iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
  $SUDO iptables -I INPUT 5 -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT 2>/dev/null || $SUDO iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
  $SUDO iptables -I INPUT 5 -p udp -m state --state NEW -m udp --dport 443 -j ACCEPT 2>/dev/null || $SUDO iptables -I INPUT 1 -p udp --dport 443 -j ACCEPT
  
  if command -v netfilter-persistent &> /dev/null; then
    $SUDO netfilter-persistent save || true
  fi
fi

if command -v firewall-cmd &> /dev/null; then
  # For Oracle Linux / CentOS / RHEL images
  $SUDO firewall-cmd --zone=public --permanent --add-port=80/tcp || true
  $SUDO firewall-cmd --zone=public --permanent --add-port=443/tcp || true
  $SUDO firewall-cmd --zone=public --permanent --add-port=443/udp || true
  $SUDO firewall-cmd --reload || true
fi

# 5. Launch containers
echo " Pulling latest images & starting n8n stack..."
$SUDO docker compose pull
$SUDO docker compose up -d --remove-orphans

echo ""
echo "=========================================="
echo " n8n Stack Started Successfully!"
echo "=========================================="
$SUDO docker compose ps
echo ""
echo "Note: Make sure your DNS 'A' record is pointing to this instance's Public IP."
echo "Caddy will automatically obtain Let's Encrypt certificates as soon as DNS resolves."
