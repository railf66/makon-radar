"""Связь с секретарём Дильнозой (сценарий в Make) через вебхук.

Radar шлёт в вебхук два вида запросов:
  action=add    — агент нажал «⭐ Дильнозе», объект надо добавить в таблицу;
  action=remove — объявление снято с OLX, строку с этим id надо удалить.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta

import aiohttp
from aiogram import Bot

from .config import OLX_BASE, config
from .db import db
from .i18n import district_name, t
from .olx import HEADERS

log = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))
# Статусы OLX, при которых объявление ещё живое
ACTIVE = {"active", "new", "limited"}


def listing_payload(item: dict, agent: str) -> dict:
    """Объявление простыми полями на русском, чтобы в Make их было легко разложить по столбцам."""
    district = district_name(item["district"], "ru") if item.get("district") else item.get("district_raw")
    return {
        "action": "add",
        "id": item["id"],
        "added_at": datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M"),
        "added_by": agent,
        "deal": t(f"deal_{item['deal']}", "ru"),
        "type": t(f"ptype_{item['ptype']}", "ru"),
        "title": item["title"],
        "price": item.get("price_text") or "",
        "price_usd": round(item["price_usd"]) if item.get("price_usd") else None,
        "rooms": item.get("rooms"),
        "area": item.get("area"),
        "floor": item.get("floor") or "",
        "district": district or "",
        "address": item.get("district_raw") or "",
        "owner": "собственник" if item.get("is_owner") else "посредник",
        "url": item["url"],
        "photo": item.get("photo") or "",
    }


async def _post(payload: dict) -> bool:
    if not config.dilnoza_webhook:
        return False
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(config.dilnoza_webhook, json=payload,
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status >= 400:
                    log.warning("Вебхук Дильнозы ответил %s", r.status)
                    return False
                return True
    except Exception as e:
        log.warning("Вебхук Дильнозы недоступен: %s", e)
        return False


async def push_listing(item: dict, agent: str) -> bool:
    if not await _post(listing_payload(item, agent)):
        return False
    await db.add_dilnoza(item)
    return True


async def offer_alive(session: aiohttp.ClientSession, listing_id: str) -> bool | None:
    """True — объявление на OLX живое, False — снято, None — не удалось понять (не трогаем)."""
    try:
        async with session.get(f"{OLX_BASE}/api/v1/offers/{listing_id}/", headers=HEADERS,
                               timeout=aiohttp.ClientTimeout(total=30)) as r:
            if r.status in (404, 410):
                return False
            if r.status != 200:
                return None
            data = (await r.json(content_type=None)).get("data") or {}
    except Exception as e:
        log.warning("Не проверил объявление %s: %s", listing_id, e)
        return None
    status = data.get("status")
    if status is None:
        return True
    return status in ACTIVE


async def check_removed(bot: Bot) -> int:
    """Убирает из таблицы Дильнозы объекты, которые сняли с OLX. Возвращает, сколько убрано."""
    gone = []
    async with aiohttp.ClientSession() as session:
        for row in await db.dilnoza_active():
            if await offer_alive(session, row["listing_id"]) is False:
                if await _post({"action": "remove", "id": row["listing_id"]}):
                    await db.dilnoza_removed(row["listing_id"])
                    gone.append(row["title"])
            await asyncio.sleep(random.uniform(2, 5))  # бережём OLX
    if gone:
        text = "🗑 Сняты с OLX и убраны у Дильнозы:\n" + "\n".join(f"• {g}" for g in gone)
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(admin_id, text[:4000])
            except Exception:
                log.exception("Не смог написать админу %s", admin_id)
    return len(gone)


async def dilnoza_loop(bot: Bot):
    if not config.dilnoza_webhook or not config.olx_enabled:
        return
    await asyncio.sleep(600)  # не мешаем первому сбору после запуска
    while True:
        try:
            n = await check_removed(bot)
            log.info("Проверка объектов Дильнозы: убрано %s", n)
        except Exception:
            log.exception("Ошибка проверки объектов Дильнозы")
        await asyncio.sleep(config.dilnoza_check_hours * 3600 + random.uniform(0, 600))
