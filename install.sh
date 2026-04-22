#!/bin/bash
set -e

echo "=== TrustPanel Installer (Production Fixed) ==="

# -------------------------
# SYSTEM
# -------------------------
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git


# -------------------------
# PATH
# -------------------------
DEFAULT_DIR="/opt/trustpanel"
read -p "Install path [/opt/trustpanel]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-$DEFAULT_DIR}

echo "[INFO] Install path: $PROJECT_DIR"


# -------------------------
# CLONE / UPDATE
# -------------------------
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Updating repo..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "[INFO] Cloning repo..."
    rm -rf "$PROJECT_DIR"
    git clone https://github.com/danilwarhammer40000/trusttunnel_botpannel.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi


# -------------------------
# VENV
# -------------------------
echo "[INFO] Setting up venv..."

python3 -m venv "$PROJECT_DIR/venv"

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt


# -------------------------
# CONFIG
# -------------------------
read -p "BOT_TOKEN: " BOT_TOKEN
read -p "ADMIN_ID: " ADMIN_ID

cat > "$PROJECT_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
EOF


# -------------------------
# SYSTEMD (FIXED CORE ISSUE)
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
Environment=PYTHONPATH=$PROJECT_DIR

ExecStart=$PROJECT_DIR/venv/bin/python -m bot.bot

Restart=always
RestartSec=3

User=root

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF


# -------------------------
# START
# -------------------------
systemctl daemon-reload
systemctl enable trustpanel
systemctl restart trustpanel

echo "=== INSTALL COMPLETE ==="
echo ""
echo "Logs:"
echo "journalctl -u trustpanel -f"
echo ""

systemctl status trustpanel --no-pager
