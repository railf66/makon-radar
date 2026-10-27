import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from .config import config
from .db import db
from .filters import matches
from .olx import fetch_all
from .sender import send_listing

log = logging.getLogger(__name__)

# Сколько неудачных проверок подряд терпим, прежде чем написать админу
ALERT_AFTER = 3
# Самая длинная пауза между проверками, когда OLX не отвечает
MAX_BACKOFF = 3600


def is_fresh(item: dict) -> bool:
    """OLX поднимает старые объявления наверх. Рассылаем только созданные недавно."""
    try:
        created = datetime.fromisoformat(item["created_at"])
    except (TypeError, ValueError):
        return True
    return datetime.now(timezone.utc) - created < timedelta(hours=config.fresh_hours)


async def notify_admins(bot: Bot, text: str):
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            log.exception("Не смог написать админу %s", admin_id)


async def poll_once(bot: Bot, notify: bool = True) -> int:
    items, errors = await fetch_all()
    if not items:
        raise RuntimeError("; ".join(errors) or "OLX вернул пустой список: возможно, сайт изменился")
    new = [i for i in items if await db.add_listing(i)]
    log.info("OLX: получено %s, новых %s, ошибок разделов %s", len(items), len(new), len(errors))
    if not notify:
        return len(new)
    for user in await db.active_users():
        for item in new:
            if is_fresh(item) and matches(item, user["filters"]) and await db.mark_sent(user["id"], item["id"]):
                await send_listing(bot, user, item)
                await asyncio.sleep(0.05)  # лимиты Telegram
    return len(new)


async def poll_loop(bot: Bot):
    if not config.olx_enabled:
        log.warning("Сбор с OLX выключен (OLX_ENABLED=0)")
        return
    # Первый проход только наполняет базу, чтобы не завалить агентов старыми объявлениями
    first = True
    failures = 0
    alerted = False
    while True:
        delay = config.poll_interval
        try:
            await poll_once(bot, notify=not first)
            first = False
            if alerted:
                await notify_admins(bot, "✅ Сбор с OLX снова работает.")
            failures, alerted = 0, False
        except Exception as e:
            failures += 1
            log.exception("Ошибка сбора (%s подряд)", failures)
            if failures >= ALERT_AFTER and not alerted:
                await notify_admins(
                    bot,
                    f"⚠️ OLX не отвечает уже {failures} проверки подряд.\n{str(e)[:500]}\n"
                    "Бот продолжает пробовать сам и напишет, когда сбор восстановится.",
                )
                alerted = True
            # При сбоях проверяем реже, чтобы не злить OLX
            delay = min(config.poll_interval * 2 ** min(failures, 4), MAX_BACKOFF)
        await asyncio.sleep(delay + random.uniform(0, 60))
