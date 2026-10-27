import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .db import db
from .filters import format_listing
from .i18n import t

log = logging.getLogger(__name__)


async def send_listing(bot: Bot, user: dict, item: dict):
    lang = user["lang"]
    text = format_listing(item, lang)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("open", lang), url=item["url"])]])
    try:
        if item.get("photo"):
            try:
                await bot.send_photo(user["id"], item["photo"], caption=text, parse_mode="HTML", reply_markup=kb)
                return
            except TelegramBadRequest:
                pass  # фото не загрузилось — шлём текстом
        await bot.send_message(user["id"], text, parse_mode="HTML", reply_markup=kb)
    except TelegramForbiddenError:
        log.info("Пользователь %s заблокировал бота, ставлю на паузу", user["id"])
        await db.update_user(user["id"], active=0)
