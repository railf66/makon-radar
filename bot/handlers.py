import re
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)

from .config import config
from .db import db
from .export import build_excel
from .filters import format_listing, matches
from .i18n import DISTRICTS, T, district_name, t
from .sender import send_listing

router = Router()


class S(StatesGroup):
    code = State()
    price = State()


def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🇷🇺 Русский", "lang:ru"), btn("🇺🇿 O‘zbekcha", "lang:uz")]])


def main_kb(user):
    lang = user["lang"]
    pause = t("menu_pause", lang) if user["active"] else t("menu_resume", lang)
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t("menu_filters", lang)), KeyboardButton(text=t("menu_latest", lang))],
        [KeyboardButton(text=t("menu_export", lang)), KeyboardButton(text=pause)],
        [KeyboardButton(text=t("menu_lang", lang))],
    ])


def mark(on: bool, text: str) -> str:
    return f"✅ {text}" if on else text


def filters_kb(user):
    f, lang = user["filters"], user["lang"]
    price = t("any", lang)
    if f["price_min"] or f["price_max"]:
        price = f"{f['price_min'] or 0:,}–{f['price_max'] or '∞'}".replace(",", " ")
    districts = ", ".join(district_name(d, lang) for d in f["districts"]) or t("any", lang)
    if len(districts) > 30:
        districts = f"{len(f['districts'])} ✓"
    rows = [
        [btn(mark(d in f["deal"], t(f"deal_{d}", lang)), f"tg:deal:{d}") for d in ("sale", "rent")],
        [btn(mark(p in f["ptype"], t(f"ptype_{p}", lang)), f"tg:ptype:{p}") for p in ("flat", "house", "commercial")],
        [btn(mark(r in f["rooms"], f"{r}{'+' if r == 4 else ''}"), f"tg:rooms:{r}") for r in (1, 2, 3, 4)],
        [btn(f"📍 {t('f_districts', lang)}: {districts}", "districts")],
        [btn(f"💰 {t('f_price', lang)}: {price}", "price")],
        [btn(mark(f["owner_only"], t("f_owner", lang)), "owner")],
        [btn(t("done", lang), "done")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def districts_kb(user):
    f, lang = user["filters"], user["lang"]
    keys = list(DISTRICTS)
    rows = [[btn(mark(k in f["districts"], district_name(k, lang)), f"tg:districts:{k}") for k in keys[i:i + 2]]
            for i in range(0, len(keys), 2)]
    rows.append([btn(t("back", lang), "filters")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def menu_texts(key):
    return set(T[key].values())


def pilot_over() -> bool:
    return bool(config.pilot_until and date.today() > config.pilot_until)


# --- старт и доступ ---

@router.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await db.ensure_user(msg.from_user.id, msg.from_user.full_name)
    await msg.answer(t("choose_lang", "ru"), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":")[1]
    await db.ensure_user(cb.from_user.id, cb.from_user.full_name)
    await db.update_user(cb.from_user.id, lang=lang)
    user = await db.get_user(cb.from_user.id)
    await cb.message.delete()
    if not user["authorized"]:
        if config.access_code:
            await state.set_state(S.code)
            await cb.message.answer(t("need_code", lang))
            return
        await db.update_user(cb.from_user.id, authorized=1)
        user = await db.get_user(cb.from_user.id)
    await cb.message.answer(t("welcome", lang), reply_markup=main_kb(user))
    await cb.message.answer(t("filters_title", lang), reply_markup=filters_kb(user))


@router.message(S.code)
async def check_code(msg: Message, state: FSMContext):
    user = await db.get_user(msg.from_user.id)
    if (msg.text or "").strip() != config.access_code:
        await msg.answer(t("bad_code", user["lang"]))
        return
    await state.clear()
    await db.update_user(msg.from_user.id, authorized=1)
    user = await db.get_user(msg.from_user.id)
    await msg.answer(t("welcome", user["lang"]), reply_markup=main_kb(user))
    await msg.answer(t("filters_title", user["lang"]), reply_markup=filters_kb(user))


async def authorized_user(user_id: int, answer):
    user = await db.get_user(user_id)
    if not user or not user["authorized"]:
        await answer(t("choose_lang", "ru"), reply_markup=lang_kb())
        return None
    if pilot_over() and user_id not in config.admin_ids:
        await answer(t("pilot_over", user["lang"]))
        return None
    return user


# --- фильтры ---

@router.message(F.text.in_(menu_texts("menu_filters")))
async def show_filters(msg: Message):
    if user := await authorized_user(msg.from_user.id, msg.answer):
        await msg.answer(t("filters_title", user["lang"]), reply_markup=filters_kb(user))


@router.callback_query(F.data.startswith("tg:"))
async def toggle(cb: CallbackQuery):
    _, field, value = cb.data.split(":")
    user = await db.get_user(cb.from_user.id)
    value = int(value) if field == "rooms" else value
    values = user["filters"][field]
    values.remove(value) if value in values else values.append(value)
    await db.update_user(cb.from_user.id, filters=user["filters"])
    kb = districts_kb(user) if field == "districts" else filters_kb(user)
    await cb.message.edit_reply_markup(reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "districts")
async def open_districts(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    await cb.message.edit_reply_markup(reply_markup=districts_kb(user))
    await cb.answer()


@router.callback_query(F.data == "filters")
async def back_to_filters(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    await cb.message.edit_reply_markup(reply_markup=filters_kb(user))
    await cb.answer()


@router.callback_query(F.data == "owner")
async def toggle_owner(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    user["filters"]["owner_only"] = not user["filters"]["owner_only"]
    await db.update_user(cb.from_user.id, filters=user["filters"])
    await cb.message.edit_reply_markup(reply_markup=filters_kb(user))
    await cb.answer()


@router.callback_query(F.data == "price")
async def ask_price(cb: CallbackQuery, state: FSMContext):
    user = await db.get_user(cb.from_user.id)
    await state.set_state(S.price)
    await cb.message.answer(t("price_ask", user["lang"]))
    await cb.answer()


@router.message(S.price)
async def set_price(msg: Message, state: FSMContext):
    user = await db.get_user(msg.from_user.id)
    text = (msg.text or "").replace(" ", "").replace("$", "")
    if text == "0":
        lo, hi = 0, 0
    elif m := re.fullmatch(r"(\d+)?[-–](\d+)?", text):
        lo, hi = int(m.group(1) or 0), int(m.group(2) or 0)
    else:
        await msg.answer(t("price_bad", user["lang"]))
        return
    user["filters"].update(price_min=lo, price_max=hi)
    await db.update_user(msg.from_user.id, filters=user["filters"])
    await state.clear()
    await msg.answer(t("saved", user["lang"]))
    await msg.answer(t("filters_title", user["lang"]), reply_markup=filters_kb(user))


@router.callback_query(F.data == "done")
async def filters_done(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(t("saved", user["lang"]), reply_markup=main_kb(user))
    await cb.answer()


# --- меню ---

@router.message(F.text.in_(menu_texts("menu_latest")))
async def latest(msg: Message):
    user = await authorized_user(msg.from_user.id, msg.answer)
    if not user:
        return
    found = [i for i in await db.recent_listings(days=3) if matches(i, user["filters"])][:5]
    if not found:
        await msg.answer(t("no_results", user["lang"]))
    for item in found:
        await send_listing(msg.bot, user, item)


@router.message(F.text.in_(menu_texts("menu_export")))
async def export(msg: Message):
    user = await authorized_user(msg.from_user.id, msg.answer)
    if not user:
        return
    items = [i for i in await db.recent_listings(days=7) if matches(i, user["filters"])]
    if not items:
        await msg.answer(t("no_results", user["lang"]))
        return
    data = build_excel(items, user["lang"])
    await msg.answer_document(BufferedInputFile(data, filename="olx_tashkent.xlsx"),
                              caption=f"{t('export_caption', user['lang'])}: {len(items)}")


@router.message(F.text.in_(menu_texts("menu_pause") | menu_texts("menu_resume")))
async def pause(msg: Message):
    user = await authorized_user(msg.from_user.id, msg.answer)
    if not user:
        return
    active = 0 if user["active"] else 1
    await db.update_user(msg.from_user.id, active=active)
    user["active"] = active
    await msg.answer(t("resumed" if active else "paused", user["lang"]), reply_markup=main_kb(user))


@router.message(F.text.in_(menu_texts("menu_lang")))
async def change_lang(msg: Message):
    await msg.answer(t("choose_lang", "ru"), reply_markup=lang_kb())


@router.message(Command("stats"))
async def stats(msg: Message):
    if msg.from_user.id not in config.admin_ids:
        return
    s = await db.stats()
    await msg.answer(f"Агентов: {s['users']}\nОбъявлений собрано: {s['listings']}\nОтправлено: {s['sent']}")
