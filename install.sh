#!/bin/bash
set -e

echo "=== TrustPanel Installer (Production Hardened) ==="

# -------------------------
# SYSTEM DEPENDENCIES
# -------------------------
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git


# -------------------------
# INSTALL PATH
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
read -p "Install path [/opt/trustpanel]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-$DEFAULT_DIR}

echo "[INFO] Install path: $PROJECT_DIR"


# -------------------------
# CLONE / UPDATE
# -------------------------
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Updating repository..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "[INFO] Cloning repository..."
    rm -rf "$PROJECT_DIR"
    git clone https://github.com/danilwarhammer40000/trusttunnel_botpannel.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi


# -------------------------
# VENV (SAFE)
# -------------------------
echo "[INFO] Setting up virtual environment..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt


# -------------------------
# REQUIRED CONFIG (STRICT VALIDATION)
# -------------------------
echo "[INFO] Configuration"

while true; do
    read -p "BOT_TOKEN: " BOT_TOKEN
    [ -n "$BOT_TOKEN" ] && break
    echo "BOT_TOKEN cannot be empty"
done

while true; do
    read -p "ADMIN_ID: " ADMIN_ID
    [ -n "$ADMIN_ID" ] && break
    echo "ADMIN_ID cannot be empty"
done

while true; do
    read -p "TRUSTTUNNEL_DOMAIN (e.g. example.com): " HOSTNAME
    [ -n "$HOSTNAME" ] && break
    echo "TRUSTTUNNEL_DOMAIN cannot be empty"
done


# -------------------------
# ENV FILE (SAFE OVERRIDE)
# -------------------------
echo "[INFO] Writing .env"

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$HOSTNAME
PYTHONPATH=$PROJECT_DIR
EOF


# -------------------------
# SYSTEMD (ROBUST VERSION)
# -------------------------
echo "[INFO] Creating systemd service..."

cat > /etc/systemd/system/trustpanel.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR

EnvironmentFile=$PROJECT_DIR/.env

ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot

Restart=always
RestartSec=5
StartLimitIntervalSec=0

User=root

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF


# -------------------------
# START SERVICE
# -------------------------
systemctl daemon-reload
systemctl enable trustpanel
systemctl restart trustpanel

echo "=== INSTALL COMPLETE ==="
echo ""
echo "Check logs:"
echo "journalctl -u trustpanel -f"
echo ""
systemctl status trustpanel --no-pager
