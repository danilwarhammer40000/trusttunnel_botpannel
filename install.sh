#!/bin/bash

set -e

echo "=== TrustPanel Installer ==="

# -------------------------
# SYSTEM UPDATE
# -------------------------
echo "[1/7] Updating system..."
apt update && apt upgrade -y

echo "[2/7] Installing dependencies..."
apt install -y python3 python3-venv python3-pip git

# -------------------------
# PROJECT PATH
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
read -p "Install path [/opt/trustpanel]: " input_path
PROJECT_DIR=${input_path:-$DEFAULT_DIR}

echo "[INFO] Installing to: $PROJECT_DIR"

# -------------------------
# SAFE INSTALL DIR
# -------------------------
mkdir -p $PROJECT_DIR

# очищаем ТОЛЬКО код, не трогая system
rsync -av --exclude='venv' --exclude='.git' ./ $PROJECT_DIR/

cd $PROJECT_DIR

# -------------------------
# PYTHON ENV
# -------------------------
echo "[3/7] Creating virtual environment..."

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

# -------------------------
# TRUSTTUNNEL PATH
# -------------------------
echo "[4/7] TrustTunnel path setup"

DEFAULT_TT="/opt/trusttunnel"
read -p "TrustTunnel path [/opt/trusttunnel]: " TT_PATH
TT_PATH=${TT_PATH:-$DEFAULT_TT}

# -------------------------
# ENV FILE
# -------------------------
echo "[5/7] Creating .env"

read -p "BOT_TOKEN: " BOT_TOKEN
read -p "ADMIN_ID: " ADMIN_ID

cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_ENDPOINT_BIN=$TT_PATH/trusttunnel_endpoint
EOF

# -------------------------
# SYSTEMD SERVICE
# -------------------------
echo "[6/7] Creating systemd service..."

cat > /etc/systemd/system/trustpanel.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot
Restart=always
RestartSec=3
User=root

# logs в journalctl
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# -------------------------
# START SERVICE
# -------------------------
echo "[7/7] Starting service..."

systemctl daemon-reload
systemctl enable trustpanel
systemctl restart trustpanel

echo "=== INSTALL COMPLETE ==="
echo "Check status:"
systemctl status trustpanel --no-pager