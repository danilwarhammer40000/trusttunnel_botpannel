#!/bin/bash
set -euo pipefail

echo "=== TrustPanel Installer (Production Hardened) ==="

# -------------------------
# CONFIG
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
PROJECT_DIR="${PROJECT_DIR:-$DEFAULT_DIR}"

# -------------------------
# SYSTEM DEPENDENCIES
# -------------------------
echo "[1/8] Installing system dependencies..."

export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt install -y python3 python3-venv python3-pip git curl ca-certificates

# -------------------------
# INSTALL / UPDATE
# -------------------------
echo "[2/8] Preparing install directory..."

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
# VENV (HARD FIXED)
# -------------------------
echo "[3/8] Setting up virtual environment..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# -------------------------
# INPUT VALIDATION
# -------------------------
echo "[4/8] Configuration"

read -r -p "BOT_TOKEN: " BOT_TOKEN
read -r -p "ADMIN_ID: " ADMIN_ID
read -r -p "TRUSTTUNNEL_DOMAIN: " DOMAIN

if [[ -z "$BOT_TOKEN" || -z "$ADMIN_ID" || -z "$DOMAIN" ]]; then
    echo "[ERROR] Required variables missing"
    exit 1
fi

# sanitize (CRLF / hidden chars fix)
BOT_TOKEN=$(echo "$BOT_TOKEN" | tr -d '\r')
ADMIN_ID=$(echo "$ADMIN_ID" | tr -d '\r')
DOMAIN=$(echo "$DOMAIN" | tr -d '\r')

# -------------------------
# .ENV (HARDENED WRITER)
# -------------------------
echo "[5/8] Writing .env safely..."

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
TRUSTTUNNEL_DOMAIN=$DOMAIN
PYTHONPATH=$PROJECT_DIR
EOF

chmod 600 "$PROJECT_DIR/.env"

# -------------------------
# SYSTEMD (CLEAN REINSTALL)
# -------------------------
echo "[6/8] Installing systemd service..."

SERVICE_FILE="/etc/systemd/system/trustpanel-bot.service"

cat > "$SERVICE_FILE" <<EOF
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
RestartPreventExitStatus=255

User=root
Group=root

# HARDENING
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
# SYSTEMD APPLY
# -------------------------
echo "[7/8] Reloading systemd..."

systemctl daemon-reload
systemctl stop trustpanel-bot.service 2>/dev/null || true
systemctl enable trustpanel-bot.service
systemctl restart trustpanel-bot.service

# -------------------------
# HEALTH CHECK
# -------------------------
echo "[8/8] Checking service..."

sleep 2

if systemctl is-active --quiet trustpanel-bot.service; then
    echo "✅ TRUSTPANEL BOT IS RUNNING"
else
    echo "❌ SERVICE FAILED"
    echo ""
    systemctl status trustpanel-bot.service --no-pager || true
    echo ""
    echo "LAST LOGS:"
    journalctl -u trustpanel-bot.service -n 50 --no-pager || true
fi

echo ""
echo "DONE"
echo "Logs: journalctl -u trustpanel-bot.service -f"
