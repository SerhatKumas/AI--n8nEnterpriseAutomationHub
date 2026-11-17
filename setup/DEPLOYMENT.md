# ⚡ Production-Ready n8n Deployment on Oracle Cloud Infrastructure (OCI)

This stack deploys the **latest n8n** with **Caddy** as a reverse proxy, featuring **100% free, automatic Let's Encrypt SSL certificates**, HTTP/3 QUIC support, and automatic renewal.

---

## 📋 Prerequisites Check

1. **Oracle Cloud VM**:
   - An active Compute Instance (e.g., Always Free Ampere A1 ARM with up to 4 OCPU / 24 GB RAM, or AMD E2.1.Micro) running Ubuntu 22.04 / 24.04 or Oracle Linux.
   - Public IP address assigned to the VM.
2. **Oracle Cloud Ingress Rule (Crucial)**:
   In the Oracle Cloud Console:
   - Go to **Networking** → **Virtual Cloud Networks (VCN)** → Click your VCN → **Security Lists** → **Default Security List**.
   - Add **Ingress Rules**:
     - **Source CIDR**: `0.0.0.0/0`
     - **IP Protocol**: `TCP`
     - **Destination Port Range**: `80, 443`
     - (Optional for HTTP/3) Add `UDP` rule for port `443`.
3. **Domain Name DNS**:
   - Create an **A record** in your domain DNS manager:
     - **Host**: `n8n` (or `@` for root domain)
     - **Value**: Your Oracle Cloud VM Public IP (e.g. `129.153.xx.xx`)

---

## 🚀 Quick Deployment Options

### Option A: 1-Click Remote Deployment from this Mac
If you have SSH access to your Oracle Cloud instance:

1. Update `.env` with your domain and email:
   ```bash
   DOMAIN_NAME=n8n.yourdomain.com
   SSL_EMAIL=your-email@example.com
   ```
2. Run the remote deploy script:
   ```bash
   ./remote-deploy.sh <VM_PUBLIC_IP> ubuntu ~/.ssh/your_ssh_key
   ```
   *(Replace `ubuntu` with `opc` if using Oracle Linux)*

---

### Option B: Run Directly on the VM
1. SSH into your Oracle Cloud instance:
   ```bash
   ssh -i /path/to/key ubuntu@<VM_PUBLIC_IP>
   ```
2. Clone or copy this directory into the VM:
   ```bash
   mkdir -p ~/n8n && cd ~/n8n
   ```
3. Edit `.env` with your domain and email.
4. Run the installer:
   ```bash
   chmod +x setup.sh && ./setup.sh
   ```

---

## 🛠️ Included Components

- **`docker-compose.yml`**: Official `docker.n8n.io/n8nio/n8n:latest` + `caddy:latest`
- **`Caddyfile`**: Automatic SSL, HTTP/3, and real-time execution streaming (`flush_interval -1`)
- **`setup.sh`**:
  - Automatically installs Docker & Docker Compose
  - Configures Oracle Cloud's default internal `iptables` rules to allow 80/443
  - Generates secure encryption keys
  - Starts the service with `docker compose up -d`
- **`remote-deploy.sh`**: Transfers files and runs everything remotely in one step
