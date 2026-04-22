#!/bin/bash

set -e

echo "=== TrustPanel Installer (Fixed Production Version) ==="


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
read -p "Install path [/opt/trustpanel]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-$DEFAULT_DIR}

echo "[INFO] Installing repo to: $PROJECT_DIR"


# -------------------------
# CLONE OR UPDATE
# -------------------------
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Existing repo found, pulling updates..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "[INFO] Cloning repository..."
    rm -rf "$PROJECT_DIR"
    git clone https://github.com/danilwarhammer40000/trusttunnel_botpannel.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi


# -------------------------
# VENV (RECREATE SAFE)
# -------------------------
echo "[3/7] Setting up virtual environment..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv venv
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt


# -------------------------
# MANUAL CONFIG
# -------------------------
echo "[4/7] Manual configuration"

read -p "Enter TRUSTTUNNEL HOSTNAME (e.g. example.ru): " HOSTNAME

read -p "TrustTunnel binary path [/opt/trusttunnel]: " TT_PATH
TT_PATH=${TT_PATH:-/opt/trusttunnel}

BINARY="$TT_PATH/trusttunnel_endpoint"

if [ ! -f "$BINARY" ]; then
    echo "[WARN] binary not found: $BINARY"
fi


# -------------------------
# ENV FILE (SAFE REWRITE)
# -------------------------
echo "[5/7] Creating .env"

read -p "BOT_TOKEN: " BOT_TOKEN
read -p "ADMIN_ID: " ADMIN_ID

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$HOSTNAME
TRUSTTUNNEL_ENDPOINT_BIN=$BINARY
EOF


# -------------------------
# SYSTEMD SERVICE (FIXED EXEC PATH)
# -------------------------
echo "[6/7] Creating systemd service..."

cat > /etc/systemd/system/trustpanel.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env

ExecStart=$PROJECT_DIR/venv/bin/python /opt/trustpanel/bot/bot.py

Restart=always
RestartSec=3

User=root

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF


# -------------------------
# SYSTEMD APPLY
# -------------------------
echo "[7/7] Enabling service..."

systemctl daemon-reload
systemctl enable trustpanel
systemctl restart trustpanel

echo "=== INSTALL COMPLETE ==="
echo ""
echo "Update command:"
echo "cd $PROJECT_DIR && git pull && /opt/trustpanel/venv/bin/pip install -r requirements.txt && systemctl restart trustpanel"
echo ""

systemctl status trustpanel --no-pager
