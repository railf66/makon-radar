#!/bin/sh
# Автообновление: если в GitHub (ветка main) появился новый код — git pull и deploy/install.sh.
# Запускается таймером olx-autoupdate.timer каждые 5 минут (его ставит install.sh).
# Вручную: sh deploy/autoupdate.sh   Лог: /var/log/olx-autoupdate.log
REPO=$(cd "$(dirname "$0")/.." && pwd)
LOG=/var/log/olx-autoupdate.log
ENV=/opt/olx-bot/.env
FAILED=/var/lib/olx-autoupdate.failed

# Не запускаемся дважды одновременно
exec 9>/run/olx-autoupdate.lock
flock -n 9 || exit 0

notify() {
    TOKEN=$(grep '^BOT_TOKEN=' "$ENV" | cut -d= -f2-)
    for ADMIN in $(grep '^ADMIN_IDS=' "$ENV" | cut -d= -f2- | tr ',' ' '); do
        curl -s -m 20 "https://api.telegram.org/bot$TOKEN/sendMessage" \
            --data-urlencode "chat_id=$ADMIN" --data-urlencode "text=$1" >/dev/null || true
    done
}

fail() {
    echo "$NEW" > "$FAILED"   # про эту версию больше не пишем, ждём следующую
    echo "$(date '+%F %T') ОШИБКА: $1" >> "$LOG"
    notify "❌ Автообновление Makon Radar не удалось: $1
Последние строки лога:
$(tail -n 8 "$LOG")"
    exit 1
}

cd "$REPO" || exit 1
git fetch -q origin main >> "$LOG" 2>&1 || exit 0   # нет связи с GitHub — попробуем через 5 минут
OLD=$(git rev-parse HEAD)
NEW=$(git rev-parse origin/main)
[ "$OLD" = "$NEW" ] && exit 0
[ "$(cat "$FAILED" 2>/dev/null)" = "$NEW" ] && exit 0   # эта версия уже не встала, админ знает

echo "$(date '+%F %T') обновление $OLD -> $NEW" >> "$LOG"
git merge-base --is-ancestor HEAD origin/main \
    || fail "код на сервере отличается от GitHub (правили вручную?). Проверьте: cd $REPO; git status; git log -3"
git pull -q --ff-only origin main >> "$LOG" 2>&1 \
    || fail "git pull не прошёл (изменены файлы на сервере?). Проверьте: cd $REPO; git status"
sh deploy/install.sh < /dev/null >> "$LOG" 2>&1 || fail "deploy/install.sh завершился с ошибкой"
sleep 10
systemctl is-active -q olx-bot || fail "после обновления бот не запустился (journalctl -u olx-bot -n 50)"
rm -f "$FAILED"
echo "$(date '+%F %T') готово" >> "$LOG"
notify "✅ Makon Radar обновлён: $(git log -1 --format=%s)"
