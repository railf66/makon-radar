#!/bin/sh
# Поменять одну настройку бота и перезапустить его: sh deploy/set.sh ИМЯ ЗНАЧЕНИЕ
# Пример: sh deploy/set.sh CONTACT @railf66
set -e
[ -n "$1" ] && [ -n "$2" ] || { echo "Нужно: sh deploy/set.sh ИМЯ ЗНАЧЕНИЕ"; exit 1; }
F=/opt/olx-bot/.env
if grep -q "^$1=" "$F"; then
    sed -i "s|^$1=.*|$1=$2|" "$F"
else
    echo "$1=$2" >> "$F"
fi
systemctl restart olx-bot
echo "Готово: $1=$2"
