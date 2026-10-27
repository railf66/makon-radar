"""Тестовая рассылка без OLX: python -m bot.demo
Кладёт в базу 3 выдуманных объявления (с пометкой ТЕСТ) и рассылает их агентам по их фильтрам."""
import asyncio
import random

from aiogram import Bot

from .config import config
from .db import db
from .filters import matches
from .sender import send_listing

SAMPLES = [
    dict(deal="sale", ptype="flat", title="ТЕСТ: 2-комн. квартира, Юнусабад, 4 квартал", price_usd=68000,
         price_text="68 000 у.е.", rooms=2, area=58, floor="5/9", district="yunusabad",
         district_raw="Ташкент, Юнусабадский район", is_owner=1),
    dict(deal="rent", ptype="flat", title="ТЕСТ: 1-комн. квартира в аренду, Чиланзар", price_usd=350,
         price_text="350 у.е./мес", rooms=1, area=38, floor="2/4", district="chilanzar",
         district_raw="Ташкент, Чиланзарский район", is_owner=0),
    dict(deal="sale", ptype="house", title="ТЕСТ: дом 6 соток, Мирзо-Улугбек", price_usd=185000,
         price_text="185 000 у.е.", rooms=5, area=160, floor=None, district="mirzo",
         district_raw="Ташкент, Мирзо-Улугбекский район", is_owner=1),
]


async def main():
    await db.connect()
    bot = Bot(config.bot_token)
    sent = 0
    try:
        users = await db.active_users()
        for s in SAMPLES:
            item = {**s, "id": f"demo-{random.randint(10**6, 10**7)}", "url": "https://www.olx.uz/nedvizhimost/",
                    "photo": None, "created_at": None}
            await db.add_listing(item)
            for u in users:
                if matches(item, u["filters"]) and await db.mark_sent(u["id"], item["id"]):
                    await send_listing(bot, u, item)
                    sent += 1
        print(f"Агентов: {len(users)}, отправлено: {sent}")
    finally:
        await bot.session.close()
        await db.close()


asyncio.run(main())
