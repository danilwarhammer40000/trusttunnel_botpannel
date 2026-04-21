#!/bin/bash

set -e

echo "=== TrustPanel Installer (Git-based) ==="

# -------------------------
# SYSTEM UPDATE
# -------------------------
echo "[1/6] Updating system..."
apt update && apt upgrade -y

echo "[2/6] Installing dependencies..."
apt install -y python3 python3-venv python3-pip git


# -------------------------
# PROJECT PATH (GIT INSTALL)
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
read -p "Install path [/opt/trustpanel]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-$DEFAULT_DIR}

echo "[INFO] Installing repo to: $PROJECT_DIR"

# если уже есть — обновляем
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Existing repo found, pulling updates..."
    cd $PROJECT_DIR
    git pull
else
    echo "[INFO] Cloning repository..."
    rm -rf $PROJECT_DIR
    git clone https://github.com/danilwarhammer40000/trusttunnel_botpannel.git $PROJECT_DIR
    cd $PROJECT_DIR
fi


# -------------------------
# PYTHON ENV
# -------------------------
echo "[3/6] Creating virtual environment..."

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt


# -------------------------
# MANUAL CONFIG (IMPORTANT FIX)
# -------------------------
echo "[4/6] Manual configuration"

read -p "Enter TRUSTTUNNEL HOSTNAME (e.g. pelevindmy.ru): " HOSTNAME

read -p "TrustTunnel binary path [/opt/trusttunnel]: " TT_PATH
TT_PATH=${TT_PATH:-/opt/trusttunnel}

BINARY="$TT_PATH/trusttunnel_endpoint"

if [ ! -f "$BINARY" ]; then
    echo "[WARN] binary not found: $BINARY (fallback mode enabled)"
fi


# -------------------------
# ENV FILE
# -------------------------
echo "[5/6] Creating .env"

read -p "BOT_TOKEN: " BOT_TOKEN
read -p "ADMIN_ID: " ADMIN_ID

cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$HOSTNAME
TRUSTTUNNEL_ENDPOINT_BIN=$BINARY
EOF


# -------------------------
# SYSTEMD SERVICE
# -------------------------
echo "[6/6] Creating systemd service..."

cat > /etc/systemd/system/trustpanel.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot
Restart=always
RestartSec=3
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF


systemctl daemon-reload
systemctl enable trustpanel
systemctl restart trustpanel

echo "=== INSTALL COMPLETE ==="
echo "Use for updates:"
echo "cd $PROJECT_DIR && git pull && systemctl restart trustpanel"
systemctl status trustpanel --no-pager