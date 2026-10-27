"""Сбор объявлений с OLX.uz.

OLX не даёт открытого API для чтения объявлений, поэтому берём те же данные,
что получает сайт в браузере (внутренний JSON api/v1/offers).
ВАЖНО: структура ответа ещё не проверена на живом olx.uz (нет доступа из среды
разработки). Разбор написан осторожно и проверяется командой `python -m bot.check_olx`.
"""
import asyncio
import logging
import random
import re

import aiohttp

from .config import OLX_BASE, OLX_CITY_ID, OLX_REGION_ID, OLX_SECTIONS, config
from .i18n import DISTRICTS

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru,uz;q=0.9",
}

# Слова, по которым видно посредника, даже если OLX пишет «частное лицо»
AGENT_WORDS = [
    "агентств", "риелтор", "риэлтор", "realtor", "rieltor", "agentlik", "комисси",
    "услуги агент", "vositachi xizmat",
]


def _param(offer: dict, *keys):
    for p in offer.get("params", []):
        if p.get("key") in keys:
            return p.get("value") or {}
    return {}


def _num(v):
    if v is None:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", str(v).replace(" ", ""))
    return float(m.group().replace(",", ".")) if m else None


def _floor(offer: dict) -> str | None:
    floor = _num(_param(offer, "floor").get("key"))
    total = _num(_param(offer, "total_floors").get("key"))
    if floor and total:
        return f"{floor:g}/{total:g}"
    return f"{floor:g}" if floor else None


def detect_district(text: str) -> str | None:
    low = (text or "").lower()
    for key, (_, _, aliases) in DISTRICTS.items():
        if any(a in low for a in aliases):
            return key
    return None


def detect_owner(offer: dict) -> bool:
    text = f"{offer.get('title', '')} {offer.get('description', '')}".lower()
    # Посредники часто пишут «без посредников», поэтому флаг OLX «бизнес» важнее слов
    if offer.get("business") or any(w in text for w in AGENT_WORDS):
        return False
    return True


def parse_offer(offer: dict, section: dict) -> dict:
    price = _param(offer, "price")
    amount = price.get("value")
    currency = (price.get("currency") or "").upper()
    if amount is None:
        price_usd, price_text = None, price.get("label") or ""
    elif currency in ("UZS", "СУМ", "SUM"):
        price_usd = float(amount) / config.uzs_per_usd
        price_text = price.get("label") or f"{amount:,.0f} сум".replace(",", " ")
    else:  # UYE (у.е.) или USD
        price_usd = float(amount)
        price_text = f"{amount:,.0f} у.е.".replace(",", " ")

    loc = offer.get("location") or {}
    district_raw = " ".join(
        str((loc.get(k) or {}).get("name", "")) for k in ("district", "city")
    ).strip()
    district = detect_district(district_raw) or detect_district(offer.get("title", ""))

    photos = offer.get("photos") or []
    photo = None
    if photos:
        photo = photos[0].get("link", "").replace("{width}", "800").replace("{height}", "600") or None

    rooms = _num(_param(offer, "number_of_rooms", "rooms", "komnat").get("key")
                 or _param(offer, "number_of_rooms", "rooms").get("label"))

    return {
        "id": str(offer["id"]),
        "deal": section["deal"],
        "ptype": section["ptype"],
        "title": offer.get("title", ""),
        "url": offer.get("url", ""),
        "price_usd": price_usd,
        "price_text": price_text,
        "rooms": int(rooms) if rooms else None,
        "area": _num(_param(offer, "total_area", "area").get("key")
                     or _param(offer, "total_area", "area").get("label")),
        "floor": _floor(offer),
        "district": district,
        "district_raw": district_raw,
        "is_owner": 1 if detect_owner(offer) else 0,
        "photo": photo,
        "created_at": offer.get("created_time") or offer.get("last_refresh_time"),
    }


async def fetch_section(session: aiohttp.ClientSession, section: dict, limit: int = 40) -> list[dict]:
    params = {"offset": 0, "limit": limit, "sort_by": "created_at:desc"}
    if section.get("category_id"):
        params["category_id"] = section["category_id"]
    if OLX_REGION_ID:
        params["region_id"] = OLX_REGION_ID
    if OLX_CITY_ID:
        params["city_id"] = OLX_CITY_ID
    async with session.get(f"{OLX_BASE}/api/v1/offers/", params=params, headers=HEADERS,
                           timeout=aiohttp.ClientTimeout(total=30)) as r:
        r.raise_for_status()
        data = await r.json()
    items = []
    for offer in data.get("data", []):
        try:
            items.append(parse_offer(offer, section))
        except Exception:  # одно кривое объявление не должно ломать весь сбор
            log.exception("Не разобрал объявление %s", offer.get("id"))
    return items


async def fetch_all() -> tuple[list[dict], list[str]]:
    """Возвращает (объявления, ошибки по разделам)."""
    result, errors = [], []
    async with aiohttp.ClientSession() as session:
        for section in OLX_SECTIONS:
            try:
                result += await fetch_section(session, section)
            except Exception as e:
                log.warning("Раздел %s: ошибка %s", section["path"], e)
                errors.append(f"{section['path']}: {e}")
            await asyncio.sleep(random.uniform(2, 5))  # бережём OLX, не спамим запросами
    return result, errors
