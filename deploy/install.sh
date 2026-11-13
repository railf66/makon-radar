#!/bin/sh
# Установка бота на Ubuntu 22.04/24.04. Запуск от root из папки с кодом бота:
#   sh deploy/install.sh
# Повторный запуск обновляет код и сохраняет настройки (.env) и базу.
set -e
apt-get update -y && apt-get install -y python3 python3-venv git curl
id olxbot >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin olxbot
mkdir -p /opt/olx-bot
cp -r main.py requirements.txt bot /opt/olx-bot/
[ -f /opt/olx-bot/.env ] || cp .env.example /opt/olx-bot/.env
# Спрашиваем токен, пока в .env нет настоящего (в том числе если прошлый запуск прервался)
if grep -q '^BOT_TOKEN=123456:ABC' /opt/olx-bot/.env || ! grep -q '^BOT_TOKEN=..*' /opt/olx-bot/.env; then
    printf "Токен бота от @BotFather: " ; read -r TOKEN < /dev/tty
    printf "Telegram id админов через запятую: " ; read -r ADMINS < /dev/tty
    sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=$TOKEN|; s|^ADMIN_IDS=.*|ADMIN_IDS=$ADMINS|" /opt/olx-bot/.env
fi
python3 -m venv /opt/olx-bot/.venv
/opt/olx-bot/.venv/bin/pip install -q -r /opt/olx-bot/requirements.txt
chown -R olxbot:olxbot /opt/olx-bot && chmod 600 /opt/olx-bot/.env
cp deploy/olx-bot.service /etc/systemd/system/olx-bot.service
systemctl daemon-reload && systemctl enable olx-bot && systemctl restart olx-bot
# Автообновление из GitHub каждые 5 минут (deploy/autoupdate.sh)
cat > /etc/systemd/system/olx-autoupdate.service <<UNIT
[Unit]
Description=Makon Radar - автообновление из GitHub
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/sh $(pwd)/deploy/autoupdate.sh
UNIT
cp deploy/olx-autoupdate.timer /etc/systemd/system/olx-autoupdate.timer
systemctl daemon-reload && systemctl enable --now olx-autoupdate.timer
sleep 5 && systemctl --no-pager status olx-bot | head -5
echo "Готово. Логи: journalctl -u olx-bot -f   Настройки: nano /opt/olx-bot/.env"
echo "Автообновление из GitHub включено (каждые 5 минут). Лог: /var/log/olx-autoupdate.log"
