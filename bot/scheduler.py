import asyncio
import logging
import random
from datetime import date, datetime, timedelta, timezone

from aiogram import Bot

from .config import config
from .db import db
from .filters import matches
from .olx import fetch_all
from .sender import send_listing
from .billing import user_level
from .handlers import agency_over, fmt_date, tariff_kb, trial_over
from .i18n import t

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
    duplicates = set()
    for item in new:
        try:
            if await db.is_duplicate(item):
                duplicates.add(item["id"])
        except Exception:
            log.exception("Не проверил повтор %s", item.get("id"))
    for user in await db.active_users():
        if trial_over(user):
            continue  # срок закончился: этому агенту больше не шлём
        level = user_level(user)
        if level == "lite":
            continue  # Лайт получает подборку раз в час (send_digests)
        for item in new:
            if level == "pro" and item["id"] in duplicates:
                continue  # Pro: тот же объект, выложенный заново, не присылаем
            if is_fresh(item) and matches(item, user["filters"]) and await db.mark_sent(user["id"], item["id"]):
                await send_listing(bot, user, item)
                await asyncio.sleep(0.05)  # лимиты Telegram
    return len(new)


# Сколько объявлений максимум в одной подборке Лайт
DIGEST_MAX = 10


async def send_digests(bot: Bot):
    """Лайт: раз в час присылаем подборку новых объявлений по выбранным районам (до 3)."""
    now = datetime.now(timezone.utc)
    for user in await db.active_users():
        if user_level(user) != "lite" or trial_over(user):
            continue
        last = user.get("last_digest")
        if not last:
            # Первый раз только запоминаем время, чтобы не прислать старое
            await db.update_user(user["id"], last_digest=now.isoformat())
            continue
        if now - datetime.fromisoformat(last) < timedelta(minutes=config.lite_digest_minutes):
            continue
        await db.update_user(user["id"], last_digest=now.isoformat())
        if not user["filters"]["districts"]:
            continue  # на Лайте без выбранных районов подборку не шлём
        found = []
        for item in await db.listings_since(last):
            if is_fresh(item) and matches(item, user["filters"]) and await db.mark_sent(user["id"], item["id"]):
                found.append(item)
        if not found:
            continue
        lang = user["lang"]
        try:
            await bot.send_message(user["id"], t("digest_head", lang).format(n=len(found)))
        except Exception:
            log.warning("Не смог отправить подборку %s", user["id"])
            continue
        for item in found[-DIGEST_MAX:]:
            await send_listing(bot, user, item)
            await asyncio.sleep(0.05)
        if len(found) > DIGEST_MAX:
            await bot.send_message(user["id"], t("digest_more", lang).format(n=len(found) - DIGEST_MAX))


async def check_trials(bot: Bot):
    """Срок общий на агентство. За WARN_DAYS дней до конца напоминаем сотрудникам об оплате,
    когда срок вышел, сообщаем им и админу."""
    soon = (date.today() + timedelta(days=config.warn_days)).isoformat()
    for agency in await db.agencies():
        until = agency.get("until")
        if not until:
            continue
        members = await db.agency_members(agency["id"])
        over = agency_over(agency)
        if not over and until <= soon and agency["warned"] < 1:
            for user in members:
                try:
                    await bot.send_message(user["id"], t("access_soon", user["lang"]).format(date=fmt_date(until)),
                                           reply_markup=tariff_kb(user["lang"]))
                except Exception:
                    log.warning("Не смог предупредить %s", user["id"])
            await notify_admins(bot, f"⏰ У агентства «{agency['name']}» (№{agency['id']}) доступ заканчивается "
                                     f"{fmt_date(until)}. Напоминание об оплате отправлено.\n"
                                     f"Продлить вручную: /extend {agency['id']} 30")
            await db.update_agency(agency["id"], warned=1)
        elif over and agency["warned"] < 2:
            for user in members:
                try:
                    await bot.send_message(user["id"], t("pilot_over", user["lang"]), reply_markup=tariff_kb(user["lang"]))
                except Exception:
                    log.warning("Не смог сообщить %s об окончании срока", user["id"])
            await notify_admins(bot, f"⛔ У агентства «{agency['name']}» (№{agency['id']}) закончился доступ, "
                                     f"рассылка остановлена. Продлить вручную: /extend {agency['id']} 30")
            await db.update_agency(agency["id"], warned=2)


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
            await check_trials(bot)
        except Exception:
            log.exception("Ошибка проверки пробных периодов")
        try:
            await send_digests(bot)
        except Exception:
            log.exception("Ошибка подборки Лайт")
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
