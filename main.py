import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import config
from bot.db import db
from bot.handlers import router
from bot.i18n import COMMANDS
from bot.scheduler import poll_loop


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.bot_token:
        raise SystemExit("Нет BOT_TOKEN. Скопируйте .env.example в .env и впишите токен.")
    await db.connect()
    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    # Кнопка «Меню» у поля ввода: работает и на телефоне, и на компьютере
    for lang, code in (("ru", None), ("uz", "uz")):
        await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in COMMANDS[lang]],
                                  language_code=code)
    task = asyncio.create_task(poll_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
