#!/bin/bash

set -e

echo "=============================="
echo " TRUSTPANEL INSTALLER"
echo "=============================="

# ---------------- SYSTEM ----------------
echo "[1/7] Updating system..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl

# ---------------- PROJECT DIR ----------------
PROJECT_DIR=$(pwd)

echo "[2/7] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# ---------------- INPUT ----------------
echo "[3/7] Configuration setup"

read -p "BOT TOKEN: " BOT_TOKEN
read -p "ADMIN ID: " ADMIN_ID

read -p "TrustTunnel path [/opt/trusttunnel]: " TT_PATH
TT_PATH=${TT_PATH:-/opt/trusttunnel}

echo "[4/7] Detecting TrustTunnel..."

ENDPOINT_BIN="$TT_PATH/trusttunnel_endpoint"
VPN_FILE="$TT_PATH/vpn.toml"
HOSTS_FILE="$TT_PATH/hosts.toml"

if [ ! -f "$ENDPOINT_BIN" ]; then
    echo "WARNING: endpoint not found at $ENDPOINT_BIN"
    echo "Generator will fallback mode (dev mode)"
fi

# ---------------- ENV ----------------
echo "[5/7] Creating .env"

cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_PATH=$TT_PATH
TRUSTTUNNEL_ENDPOINT_BIN=$ENDPOINT_BIN
VPN_FILE=$VPN_FILE
HOSTS_FILE=$HOSTS_FILE
EOF

# ---------------- SYSTEMD ----------------
echo "[6/7] Creating systemd service"

cat > /etc/systemd/system/trustpanel.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot
Restart=always
RestartSec=5
User=root
EnvironmentFile=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable trustpanel

# ---------------- FINAL ----------------
echo "[7/7] Starting service..."
systemctl start trustpanel

echo "=============================="
echo " INSTALL COMPLETE"
echo "=============================="
echo "Bot is running via systemd"
echo "Check: systemctl status trustpanel"