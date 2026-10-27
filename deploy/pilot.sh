#!/bin/sh
# Настройка пилота: sh deploy/pilot.sh КОД ДАТА_ОКОНЧАНИЯ
# Пример: sh deploy/pilot.sh makon2026 2026-11-10
set -e
[ -n "$1" ] && [ -n "$2" ] || { echo "Нужно: sh deploy/pilot.sh КОД ГГГГ-ММ-ДД"; exit 1; }
sed -i "s|^ACCESS_CODE=.*|ACCESS_CODE=$1|; s|^PILOT_UNTIL=.*|PILOT_UNTIL=$2|" /opt/olx-bot/.env
systemctl restart olx-bot
echo "Готово: код доступа $1, пилот до $2 включительно."
