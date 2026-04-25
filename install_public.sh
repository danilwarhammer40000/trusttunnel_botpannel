#!/bin/bash

set -e

PROJECT_DIR="/opt/trustpanel"

echo "=== TrustPanel PUBLIC BOT INSTALL ==="

# --- Проверка установки основной панели ---
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Основная панель не установлена в $PROJECT_DIR"
    exit 1
fi

# --- Ввод токена ---
read -p "Введите BOT TOKEN публичного бота: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Токен не может быть пустым"
    exit 1
fi

# --- Переход в проект ---
cd $PROJECT_DIR

# --- Создание .env ---
ENV_FILE="$PROJECT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    touch $ENV_FILE
fi

# --- Добавление токена ---
grep -v "PUBLIC_BOT_TOKEN=" $ENV_FILE > $ENV_FILE.tmp || true
mv $ENV_FILE.tmp $ENV_FILE

echo "PUBLIC_BOT_TOKEN=$BOT_TOKEN" >> $ENV_FILE

echo "✅ Токен сохранен"

# --- Установка зависимостей ---
$PROJECT_DIR/venv/bin/pip install aiogram python-dotenv

# --- Создание systemd сервиса ---
SERVICE_FILE="/etc/systemd/system/trustpanel-public-bot.service"

cat <<EOF > $SERVICE_FILE
[Unit]
Description=TrustPanel Public Bot
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python -m public_bot.bot
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# --- Перезапуск systemd ---
systemctl daemon-reload
systemctl enable trustpanel-public-bot
systemctl restart trustpanel-public-bot

echo "🚀 PUBLIC BOT УСТАНОВЛЕН И ЗАПУЩЕН"
