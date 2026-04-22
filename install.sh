#!/bin/bash
set -e

echo "=== TrustPanel Installer (Production Stable Build) ==="

# -------------------------
# SYSTEM DEPENDENCIES
# -------------------------
echo "[1/7] Installing system dependencies..."
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
# CLONE / UPDATE REPO
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
# VENV SETUP
# -------------------------
echo "[2/7] Setting up virtual environment..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt


# -------------------------
# REQUIRED CONFIG
# -------------------------
echo "[3/7] Configuration"

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
# ENV FILE
# -------------------------
echo "[4/7] Writing .env"

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$HOSTNAME
PYTHONPATH=$PROJECT_DIR
EOF


# -------------------------
# SYSTEMD INSTALL (FIXED)
# -------------------------
echo "[5/7] Installing systemd units..."

SYSTEMD_SRC="$PROJECT_DIR/systemd"

if [ -d "$SYSTEMD_SRC" ]; then
    cp -f "$SYSTEMD_SRC"/*.service /etc/systemd/system/ 2>/dev/null || true
    cp -f "$SYSTEMD_SRC"/*.timer /etc/systemd/system/ 2>/dev/null || true
else
    echo "[WARN] systemd directory not found in repo"
fi


# fallback: ensure bot service exists (if repo missing it)
cat > /etc/systemd/system/trustpanel-bot.service <<EOF
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
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF


# -------------------------
# APPLY SYSTEMD
# -------------------------
echo "[6/7] Reloading systemd..."

systemctl daemon-reload

systemctl enable trustpanel-bot.service
systemctl restart trustpanel-bot.service

systemctl enable trustpanel-cleanup.timer 2>/dev/null || true
systemctl start trustpanel-cleanup.timer 2>/dev/null || true


# -------------------------
# FINAL STATUS
# -------------------------
echo "[7/7] Installation complete"

echo ""
echo "Status:"
systemctl status trustpanel-bot.service --no-pager || true

echo ""
echo "Timer status:"
systemctl list-timers | grep trustpanel || true

echo ""
echo "Logs:"
echo "journalctl -u trustpanel-bot.service -f"
echo ""
