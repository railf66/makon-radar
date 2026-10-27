"""Проверка, что сбор с OLX.uz работает: python -m bot.check_olx"""
import asyncio
import json

from .olx import fetch_all


async def main():
    items, errors = await fetch_all()
    for e in errors:
        print('Ошибка:', e)
    print(f"Получено объявлений: {len(items)}")
    for i in items[:5]:
        print(json.dumps(i, ensure_ascii=False, indent=1))
    no_district = sum(1 for i in items if not i["district"])
    print(f"Без района: {no_district}, собственников: {sum(i['is_owner'] for i in items)}")


asyncio.run(main())
