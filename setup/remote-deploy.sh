#!/bin/bash
set -euo pipefail

# ==============================================================================
# One-Command Remote Deployer from Local Mac/Linux to Oracle Cloud VM
# Usage: ./remote-deploy.sh <VM_PUBLIC_IP> [SSH_USER: default ubuntu] [SSH_KEY_PATH: default ~/.ssh/id_ed25519 or id_rsa]
# ==============================================================================

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <VM_PUBLIC_IP> [SSH_USER] [SSH_KEY_PATH]"
  echo "Example: $0 129.153.10.20 ubuntu ~/.ssh/id_ed25519"
  exit 1
fi

SERVER_IP="$1"
SSH_USER="${2:-ubuntu}"
SSH_KEY="${3:-}"

SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
if [ -n "$SSH_KEY" ]; then
  SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Connecting to $SSH_USER@$SERVER_IP..."

# 1. Create target directory on server
ssh $SSH_OPTS "$SSH_USER@$SERVER_IP" "mkdir -p ~/n8n"

# 2. Copy files to server
echo "📦 Copying n8n configuration files to server..."
scp $SSH_OPTS "$SCRIPT_DIR/docker-compose.yml" "$SCRIPT_DIR/Caddyfile" "$SCRIPT_DIR/.env" "$SCRIPT_DIR/setup.sh" "$SSH_USER@$SERVER_IP:~/n8n/"

# 3. Execute setup script on server
echo "⚙️  Running automated setup on server..."
ssh $SSH_OPTS "$SSH_USER@$SERVER_IP" "cd ~/n8n && chmod +x setup.sh && ./setup.sh"

echo "✅ Remote deployment complete!"
