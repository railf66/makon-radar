#!/bin/sh
# Установка бота на Ubuntu 22.04/24.04. Запуск от root из папки с кодом бота:
#   sh deploy/install.sh
# Повторный запуск обновляет код и сохраняет настройки (.env) и базу.
set -e
apt-get update -y && apt-get install -y python3 python3-venv
id olxbot >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin olxbot
mkdir -p /opt/olx-bot
cp -r main.py requirements.txt bot /opt/olx-bot/
if [ ! -f /opt/olx-bot/.env ]; then
    cp .env.example /opt/olx-bot/.env
    printf "Токен бота от @BotFather: " ; read -r TOKEN < /dev/tty
    printf "Telegram id админов через запятую: " ; read -r ADMINS < /dev/tty
    sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=$TOKEN|; s|^ADMIN_IDS=.*|ADMIN_IDS=$ADMINS|" /opt/olx-bot/.env
fi
python3 -m venv /opt/olx-bot/.venv
/opt/olx-bot/.venv/bin/pip install -q -r /opt/olx-bot/requirements.txt
chown -R olxbot:olxbot /opt/olx-bot && chmod 600 /opt/olx-bot/.env
cp deploy/olx-bot.service /etc/systemd/system/olx-bot.service
systemctl daemon-reload && systemctl enable olx-bot && systemctl restart olx-bot
sleep 5 && systemctl --no-pager status olx-bot | head -5
echo "Готово. Логи: journalctl -u olx-bot -f   Настройки: nano /opt/olx-bot/.env"
