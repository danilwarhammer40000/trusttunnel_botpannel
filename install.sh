#!/bin/bash
set -euo pipefail

echo "=== TrustPanel Installer (Final + API) ==="

# -------------------------
# CONFIG
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
PROJECT_DIR="${PROJECT_DIR:-$DEFAULT_DIR}"

# -------------------------
# SYSTEM DEPENDENCIES
# -------------------------
echo "[1/9] Installing system dependencies..."

export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt install -y python3 python3-venv python3-pip git curl ca-certificates

# -------------------------
# INSTALL / UPDATE
# -------------------------
echo "[2/9] Preparing install directory..."

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Updating repository..."
    cd "$PROJECT_DIR"
    git fetch --all
    git reset --hard origin/main
    git pull --ff-only
else
    echo "[INFO] Cloning repository..."
    rm -rf "$PROJECT_DIR"
    git clone https://github.com/danilwarhammer40000/trusttunnel_botpannel.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# -------------------------
# VENV
# -------------------------
echo "[3/9] Setting up virtual environment..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt


# -------------------------
# INPUT
# -------------------------
echo "[4/9] Configuration"

read -r -p "BOT_TOKEN: " BOT_TOKEN
read -r -p "ADMIN_ID: " ADMIN_ID
read -r -p "TRUSTTUNNEL_DOMAIN: " DOMAIN

if [[ -z "$BOT_TOKEN" || -z "$ADMIN_ID" || -z "$DOMAIN" ]]; then
    echo "[ERROR] Required variables missing"
    exit 1
fi

BOT_TOKEN=$(echo "$BOT_TOKEN" | tr -d '\r')
ADMIN_ID=$(echo "$ADMIN_ID" | tr -d '\r')
DOMAIN=$(echo "$DOMAIN" | tr -d '\r')

# -------------------------
# ENV
# -------------------------
echo "[5/9] Writing .env..."

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$DOMAIN
PYTHONPATH=$PROJECT_DIR
EOF

chmod 600 "$PROJECT_DIR/.env"

# -------------------------
# SYSTEMD BOT
# -------------------------
echo "[6/9] Installing bot service..."

cat > /etc/systemd/system/trustpanel-bot.service <<EOF
[Unit]
Description=TrustPanel Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot

Restart=always
RestartSec=5
User=root
Group=root

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# -------------------------
# OPTIONAL SYSTEMD UNITS
# -------------------------
echo "[7.1] Installing systemd units..."

install_unit () {
    local name=$1
    local src="$PROJECT_DIR/systemd/$name"

    if [ -f "$src" ]; then
        echo "[INFO] Installing $name"
        cp "$src" "/etc/systemd/system/$name"
        systemctl enable "$name"
    else
        echo "[SKIP] $name not found"
    fi
}

install_unit "trustpanel-cleanup.service"
install_unit "trustpanel-backup.service"
install_unit "trustpanel-cleanup.timer"
install_unit "trustpanel-backup.timer"

# -------------------------
# SYSTEMD APPLY
# -------------------------
echo "[8/9] Reloading systemd..."

systemctl daemon-reload

systemctl stop trustpanel-bot.service 2>/dev/null || true

systemctl enable trustpanel-bot.service

systemctl restart trustpanel-bot.service

# старт таймеров (если есть)
systemctl start trustpanel-cleanup.timer 2>/dev/null || true
systemctl start trustpanel-backup.timer 2>/dev/null || true

# -------------------------
# HEALTH CHECK
# -------------------------
echo "[9/9] Checking services..."

sleep 3

echo ""
echo "=== BOT STATUS ==="
if systemctl is-active --quiet trustpanel-bot.service; then
    echo "✅ BOT RUNNING"
else
    echo "❌ BOT FAILED"
    systemctl status trustpanel-bot.service --no-pager || true
fi

echo ""
echo "=== STATUS ==="
systemctl list-timers | grep trustpanel || true

echo ""
echo "DONE"
echo "Bot logs: journalctl -u trustpanel-bot.service -f"
