"""Передача объекта секретарю Дильнозе (сценарий в Make) через вебхук."""
import logging
from datetime import datetime, timezone, timedelta

import aiohttp

from .config import config
from .i18n import district_name, t

log = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))


def listing_payload(item: dict, agent: str) -> dict:
    """Объявление простыми полями на русском, чтобы в Make их было легко разложить по столбцам."""
    district = district_name(item["district"], "ru") if item.get("district") else item.get("district_raw")
    return {
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


async def push_listing(item: dict, agent: str) -> bool:
    if not config.dilnoza_webhook:
        return False
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(config.dilnoza_webhook, json=listing_payload(item, agent),
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status >= 400:
                    log.warning("Вебхук Дильнозы ответил %s", r.status)
                    return False
                return True
    except Exception as e:
        log.warning("Вебхук Дильнозы недоступен: %s", e)
        return False
