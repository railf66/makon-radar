import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import config
from bot.db import db
from bot.handlers import router
from bot.scheduler import poll_loop


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.bot_token:
        raise SystemExit("Нет BOT_TOKEN. Скопируйте .env.example в .env и впишите токен.")
    await db.connect()
    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    task = asyncio.create_task(poll_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
