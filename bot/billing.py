"""Тарифы и оплата переводом на карту.

Оплата подтверждается админом вручную (кнопка «Подтвердить»), после чего
бот записывает её в таблицу «Makon Radar — подписчики» через вебхук Make.
"""
import logging
from datetime import date, datetime, timedelta, timezone

import aiohttp

from .config import config
from .i18n import DISTRICTS, district_name, t

log = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))


def money(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def level_name(level: str | None, lang: str) -> str:
    return t(f"level_{level}", lang) if level else t("level_trial", lang)


def user_level(user: dict) -> str:
    """Тариф берём у агентства. Пробный период работает как Стандарт."""
    agency = user.get("agency") or {}
    return agency.get("plan") or user.get("level") or "standard"


def new_until(agency: dict) -> str:
    """Продление считаем от конца текущего срока агентства, если он ещё не прошёл."""
    start = date.today()
    if agency.get("until"):
        current = date.fromisoformat(agency["until"])
        if current >= start:
            start = current
    return (start + timedelta(days=config.paid_days)).isoformat()


async def log_payment(user: dict, level: str, status: str, until: str | None, username: str | None) -> bool:
    if not config.subs_webhook:
        return False
    districts = ", ".join(district_name(d, "ru") for d in user["filters"].get("districts", []) if d in DISTRICTS)
    payload = {
        "telegram_id": str(user["id"]),
        "name": user.get("name") or "",
        "username": f"@{username}" if username else "",
        "phone": "",
        "level": t(f"level_{level}", "ru"),
        "districts": districts or "все",
        "amount": config.price(level),
        "status": status,
        "paid_until": date.fromisoformat(until).strftime("%d.%m.%Y") if until else "",
        "requested_at": datetime.now(TASHKENT).strftime("%d.%m.%Y %H:%M"),
        "comment": "перевод на карту" + (f", агентство «{user['agency']['name']}» №{user['agency']['id']}"
                                         if user.get("agency") else ""),
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(config.subs_webhook, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status >= 400:
                    log.warning("Вебхук оплат ответил %s", r.status)
                    return False
                return True
    except Exception as e:
        log.warning("Вебхук оплат недоступен: %s", e)
        return False
