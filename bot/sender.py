import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .billing import user_level
from .config import config
from .db import db
from .filters import format_listing
from .i18n import t

log = logging.getLogger(__name__)

# Pro: пометка «ниже рынка», если цена за м² ниже медианы района на столько процентов
BELOW_MARKET_PCT = 15
# и если для сравнения есть хотя бы столько объявлений
MIN_SAMPLE = 5


async def market_badge(item: dict, lang: str) -> str:
    if not (item.get("price_usd") and item.get("area") and item.get("district")):
        return ""
    median, n = await db.median_ppm(item)
    if n < MIN_SAMPLE or not median:
        return ""
    pct = round((1 - item["price_usd"] / item["area"] / median) * 100)
    return t("below_market", lang).format(pct=pct) if pct >= BELOW_MARKET_PCT else ""


async def send_listing(bot: Bot, user: dict, item: dict):
    lang = user["lang"]
    text = format_listing(item, lang)
    if user_level(user) == "pro":
        try:
            if badge := await market_badge(item, lang):
                text += "\n" + badge
        except Exception:
            log.exception("Не посчитал цену рынка для %s", item.get("id"))
    row = [InlineKeyboardButton(text=t("open", lang), url=item["url"])]
    if config.can_dilnoza(user["id"]):
        row.append(InlineKeyboardButton(text=t("dz_btn", lang), callback_data=f"dz:{item['id']}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[row])
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
