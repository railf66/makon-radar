import re
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)

from .billing import level_name, log_payment, money, new_until, user_level
from .config import LEVELS, config
from .db import db
from .dilnoza import push_listing
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
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, keyboard=[
        [KeyboardButton(text=t("menu_filters", lang)), KeyboardButton(text=t("menu_latest", lang))],
        [KeyboardButton(text=t("menu_export", lang)), KeyboardButton(text=pause)],
        [KeyboardButton(text=t("menu_team", lang)), KeyboardButton(text=t("menu_tariff", lang))],
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


def agency_over(agency: dict) -> bool:
    return bool(agency.get("until")) and date.today() > date.fromisoformat(agency["until"])


def trial_over(user: dict) -> bool:
    """Срок общий на агентство; админы без ограничений."""
    if user["id"] in config.admin_ids:
        return False
    if user.get("agency"):
        return agency_over(user["agency"])
    if not user.get("trial_until"):
        return False
    return date.today() > date.fromisoformat(user["trial_until"])


def plan_name(plan: str | None, lang: str = "ru") -> str:
    return level_name(plan if plan in LEVELS else None, lang)


def plan_seats(seats: int, lang: str) -> str:
    return t("plan_seats", lang).format(n=seats) if seats else t("plan_unlimited", lang)


def tariff_btn_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[[btn(t("choose_tariff_btn", lang), "tariff")]])


def seats_text(agency: dict, count: int) -> str:
    limit = config.seat_limit(agency)
    return f"{count}/{limit}" if limit else f"{count}/∞"


def agency_line(a: dict, count: int) -> str:
    until = f"до {fmt_date(a['until'])}" if a.get("until") else "без срока"
    mark_ = "⛔" if agency_over(a) else "✅"
    extra = f" +{a['extra_seats']} мест" if a.get("extra_seats") else ""
    return (f"{mark_} 🏢 {a['name']} — №{a['id']} — {plan_name(a['plan'])}{extra}, "
            f"сотрудников {seats_text(a, count)}, {until}, код {a['code']}")


def contact_suffix() -> str:
    return f": {config.contact}" if config.contact else ""


def fmt_date(d: str) -> str:
    return date.fromisoformat(d).strftime("%d.%m.%Y")


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
        if user.get("pending"):
            await cb.message.answer(t("trial_pending", lang))
            return
        if config.access_code:
            await state.set_state(S.code)
            await cb.message.answer(t("need_code", lang), reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[btn(t("choose_tariff_btn", lang), "tariff")]]))
            return
        await db.update_user(cb.from_user.id, authorized=1)
        user = await db.get_user(cb.from_user.id)
    await cb.message.answer(t("welcome", lang), reply_markup=main_kb(user))
    await cb.message.answer(t("filters_title", lang), reply_markup=filters_kb(user))


@router.message(S.code)
async def check_code(msg: Message, state: FSMContext):
    user = await db.get_user(msg.from_user.id)
    if user and user["authorized"]:  # уже подключён (например, оплатил тариф без кода)
        await state.clear()
        await msg.answer(t("welcome", user["lang"]), reply_markup=main_kb(user))
        return
    text = (msg.text or "").strip()
    if text.startswith("/"):
        await msg.answer(t("code_first", user["lang"]))
        return
    lang = user["lang"]
    is_admin = msg.from_user.id in config.admin_ids
    if config.access_code and text.lower() == config.access_code.lower():
        if not is_admin and config.trial_approval:
            # Код с визитки: пробный период только после одобрения админом,
            # чтобы сотрудники одного агентства не брали пробные периоды по очереди
            await state.clear()
            await db.update_user(msg.from_user.id, pending=1)
            await msg.answer(t("trial_pending", lang))
            await ask_approval(msg.bot, msg.from_user)
            return
        # Новое агентство с пробным периодом, этот человек в нём первый
        until = None if is_admin else (date.today() + timedelta(days=config.trial_days)).isoformat()
        agency = None if is_admin else await db.create_agency(msg.from_user.full_name, until)
    else:
        agency = await db.agency_by_code(text)
        if not agency:
            await msg.answer(t("bad_code", lang))
            return
        limit = config.seat_limit(agency)
        if limit and len(await db.agency_members(agency["id"])) >= limit:
            await msg.answer(t("seats_full", lang).format(name=agency["name"], limit=limit, contact=contact_suffix()),
                             reply_markup=tariff_btn_kb(lang))
            from .scheduler import notify_admins
            await notify_admins(msg.bot, f"💺 {msg.from_user.full_name} (id {msg.from_user.id}) хочет в агентство "
                                         f"«{agency['name']}», но места кончились ({limit}).\n"
                                         f"Добавить место: /plan {agency['id']} {agency['plan'] or 'trial'} {(agency['extra_seats'] or 0) + 1}")
            return
    await state.clear()
    await db.update_user(msg.from_user.id, authorized=1, trial_warned=0, pending=0,
                         agency_id=agency["id"] if agency else None)
    user = await db.get_user(msg.from_user.id)
    if agency and agency["code"] == text:
        await msg.answer(t("joined", lang).format(name=agency["name"]))
    elif agency:
        await msg.answer(t("trial_started", lang).format(date=fmt_date(agency["until"])))
        await msg.answer(t("team_code", lang).format(code=agency["code"]))
    await msg.answer(t("welcome", lang), reply_markup=main_kb(user))
    await msg.answer(t("filters_title", lang), reply_markup=filters_kb(user))


async def ask_approval(bot, tg_user):
    who = tg_user.full_name + (f" (@{tg_user.username})" if getattr(tg_user, "username", None) else "")
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("✅ Одобрить", f"ap:ok:{tg_user.id}"),
                                                btn("❌ Отказать", f"ap:no:{tg_user.id}")]])
    text = (f"🆕 Заявка на пробный период: {who}, id {tg_user.id}.\n"
            f"Если это сотрудник уже подключённого агентства, жмите «Отказать» "
            f"или добавьте его туда: /move {tg_user.id} №А (№ в /users).")
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("ap:"))
async def approval(cb: CallbackQuery):
    if cb.from_user.id not in config.admin_ids:
        await cb.answer()
        return
    _, action, uid = cb.data.split(":")
    user = await db.get_user(int(uid))
    if not user or not user.get("pending"):
        await cb.answer("Заявка уже обработана", show_alert=True)
        await cb.message.edit_reply_markup(reply_markup=None)
        return
    lang = user["lang"]
    if action == "ok":
        until = (date.today() + timedelta(days=config.trial_days)).isoformat()
        agency = await db.create_agency(user["name"], until)
        await db.update_user(user["id"], authorized=1, pending=0, trial_warned=0, agency_id=agency["id"])
        user = await db.get_user(user["id"])
        result = f"✅ Одобрено: {user['name']}, агентство №{agency['id']}, до {fmt_date(until)}."
        try:
            await cb.bot.send_message(user["id"], t("trial_started", lang).format(date=fmt_date(until)))
            await cb.bot.send_message(user["id"], t("team_code", lang).format(code=agency["code"]))
            await cb.bot.send_message(user["id"], t("welcome", lang), reply_markup=main_kb(user))
            await cb.bot.send_message(user["id"], t("filters_title", lang), reply_markup=filters_kb(user))
        except Exception:
            result += " Не смог ему написать."
    else:
        await db.update_user(user["id"], pending=0)
        result = f"❌ Отказано: {user['name']}."
        try:
            await cb.bot.send_message(user["id"], t("trial_rejected", lang) + (f"\n{config.contact}" if config.contact else ""))
        except Exception:
            pass
    await cb.message.edit_text(cb.message.text + "\n\n" + result)
    await cb.answer()


async def authorized_user(user_id: int, answer):
    user = await db.get_user(user_id)
    if not user or not user["authorized"]:
        await answer(t("choose_lang", "ru"), reply_markup=lang_kb())
        return None
    if trial_over(user):
        await answer(t("pilot_over", user["lang"]), reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[btn(t("choose_tariff_btn", user["lang"]), "tariff")]]))
        return None
    return user


# --- фильтры ---

@router.message(Command("filters"))
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
    if (field == "districts" and value not in values and user_level(user) == "lite"
            and len(values) >= config.lite_max_districts):
        await cb.answer(t("lite_max", user["lang"]), show_alert=True)
        return
    values.remove(value) if value in values else values.append(value)
    await db.update_user(cb.from_user.id, filters=user["filters"])
    kb = districts_kb(user) if field == "districts" else filters_kb(user)
    await cb.message.edit_reply_markup(reply_markup=kb)
    await cb.answer()


# --- передать объект секретарю Дильнозе ---

@router.callback_query(F.data.startswith("dz:"))
async def to_dilnoza(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    lang = user["lang"] if user else "ru"
    if not user or not user["authorized"] or trial_over(user) or not config.can_dilnoza(cb.from_user.id):
        await cb.answer()
        return
    item = await db.get_listing(cb.data.split(":", 1)[1])
    if not item or not await push_listing(item, cb.from_user.full_name):
        await cb.answer(t("dz_fail", lang), show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("open", lang), url=item["url"]),
        btn(t("dz_done_btn", lang), "dz_done"),
    ]])
    try:
        await cb.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await cb.answer(t("dz_ok", lang))


@router.callback_query(F.data == "dz_done")
async def dilnoza_done(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    await cb.answer(t("dz_ok", user["lang"] if user else "ru"))


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
    if user_level(user) == "lite" and not user["filters"]["districts"]:
        await cb.message.answer(t("lite_need_district", user["lang"]))
    await cb.answer()


# --- меню ---

@router.message(Command("menu"))
async def show_menu(msg: Message):
    """Заново показывает нижнее меню (на компьютере оно бывает скрыто)."""
    if user := await authorized_user(msg.from_user.id, msg.answer):
        await msg.answer(t("menu_shown", user["lang"]), reply_markup=main_kb(user))


@router.message(Command("latest"))
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


@router.message(Command("export"))
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


@router.message(Command("pause"))
@router.message(F.text.in_(menu_texts("menu_pause") | menu_texts("menu_resume")))
async def pause(msg: Message):
    user = await authorized_user(msg.from_user.id, msg.answer)
    if not user:
        return
    active = 0 if user["active"] else 1
    await db.update_user(msg.from_user.id, active=active)
    user["active"] = active
    await msg.answer(t("resumed" if active else "paused", user["lang"]), reply_markup=main_kb(user))


@router.message(Command("lang"))
@router.message(F.text.in_(menu_texts("menu_lang")))
async def change_lang(msg: Message):
    await msg.answer(t("choose_lang", "ru"), reply_markup=lang_kb())


@router.message(Command("team"))
@router.message(F.text.in_(menu_texts("menu_team")))
async def team(msg: Message):
    user = await authorized_user(msg.from_user.id, msg.answer)
    if not user:
        return
    lang, a = user["lang"], user["agency"]
    if not a:
        await msg.answer(t("no_team", lang))
        return
    members = await db.agency_members(a["id"])
    limit = config.seat_limit(a)
    until = t("until_date", lang).format(date=fmt_date(a["until"])) if a.get("until") else t("no_limit_date", lang)
    await msg.answer(t("team_info", lang).format(
        name=a["name"], plan=plan_name(a["plan"], lang),
        count=len(members), limit=limit or t("unlimited", lang), until=until, code=a["code"],
        members="\n".join(f"• {m['name']}" for m in members)), reply_markup=tariff_btn_kb(lang))


# --- админ: агентства, тарифы и продление ---

def admin(msg: Message) -> bool:
    return msg.from_user.id in config.admin_ids


@router.message(Command("stats"))
async def stats(msg: Message):
    if not admin(msg):
        return
    s = await db.stats()
    await msg.answer(f"Агентств: {s['agencies']}\nСотрудников: {s['users']}\n"
                     f"Объявлений собрано: {s['listings']}\nОтправлено: {s['sent']}")


@router.message(Command("users"))
async def users_list(msg: Message):
    if not admin(msg):
        return
    blocks = []
    for a in await db.agencies():
        members = await db.agency_members(a["id"])
        lines = [agency_line(a, len(members))]
        lines += [f"   • {m['name']} — id {m['id']}" for m in members]
        blocks.append("\n".join(lines))
    loose = [u for u in await db.authorized_users() if not u["agency_id"] and u["id"] not in config.admin_ids]
    if loose:
        blocks.append("Без агентства:\n" + "\n".join(f"   • {u['name']} — id {u['id']}" for u in loose))
    text = "\n\n".join(blocks) or "Агентств пока нет."
    text += ("\n\nКоманды: /extend №А 30 — продлить, /plan №А lite|standard|pro [доп.мест], "
             "/move ID №А — перенести сотрудника, /rename №А Название, /remove ID — отключить, "
             "/newagency Название — новое агентство")
    for i in range(0, len(text), 4000):  # лимит длины сообщения Telegram
        await msg.answer(text[i:i + 4000])


async def find_agency(arg: str):
    """№ агентства, а если такого нет — Telegram id сотрудника (берём его агентство)."""
    if not arg.isdigit():
        return None
    if a := await db.get_agency(int(arg)):
        return a
    user = await db.get_user(int(arg))
    return user["agency"] if user else None


@router.message(Command("extend"))
async def extend(msg: Message):
    """/extend №А ДНЕЙ, /extend №А ГГГГ-ММ-ДД или /extend №А 0 (без срока)."""
    if not admin(msg):
        return
    parts = (msg.text or "").split()
    usage = ("Как продлить: /extend №А ДНЕЙ (например /extend 3 30) или /extend 3 2026-12-31. "
             "/extend 3 0 — без срока. № агентства есть в /users (можно указать и id сотрудника).")
    if len(parts) != 3:
        await msg.answer(usage)
        return
    a = await find_agency(parts[1])
    if not a:
        await msg.answer("Нет такого агентства. Посмотрите № в /users.")
        return
    arg = parts[2]
    try:
        if arg == "0":
            until = None
        elif arg.isdigit():
            until = (date.today() + timedelta(days=int(arg))).isoformat()
        else:
            until = date.fromisoformat(arg).isoformat()
    except ValueError:
        await msg.answer(usage)
        return
    await db.update_agency(a["id"], until=until, warned=0)
    for m in await db.agency_members(a["id"]):
        await db.update_user(m["id"], active=1)
    await msg.answer(f"Готово: «{a['name']}» — " + (f"до {fmt_date(until)}" if until else "без срока") + ".")


async def trim_lite_districts(agency_id: int):
    """На Лайте у каждого сотрудника не больше LITE_MAX_DISTRICTS районов."""
    for m in await db.agency_members(agency_id):
        f = m["filters"]
        if len(f["districts"]) > config.lite_max_districts:
            f["districts"] = f["districts"][:config.lite_max_districts]
            await db.update_user(m["id"], filters=f)
        await db.update_user(m["id"], last_digest=None)


@router.message(Command("plan"))
async def set_plan(msg: Message):
    """/plan №А lite|standard|pro|trial [доп. мест] — тариф агентства без оплаты (срок не меняется)."""
    if not admin(msg):
        return
    parts = (msg.text or "").split()
    usage = (f"Как сменить тариф: /plan №А lite, /plan №А standard или /plan №А pro (trial — пробный). "
             f"Доп. места: /plan №А lite 1 (Лайт = {config.lite_seats or '∞'} сотр. + 1). № есть в /users.")
    plan = {"light": "lite", "лайт": "lite", "стандарт": "standard"}.get(parts[2].lower(), parts[2].lower()) if len(parts) > 2 else ""
    if len(parts) not in (3, 4) or plan not in LEVELS + ("trial",) or (len(parts) == 4 and not parts[3].isdigit()):
        await msg.answer(usage)
        return
    a = await find_agency(parts[1])
    if not a:
        await msg.answer("Нет такого агентства. Посмотрите № в /users.")
        return
    extra = int(parts[3]) if len(parts) == 4 else 0
    await db.update_agency(a["id"], plan=None if plan == "trial" else plan, extra_seats=extra)
    if plan == "lite":
        await trim_lite_districts(a["id"])
    a = await db.get_agency(a["id"])
    count = len(await db.agency_members(a["id"]))
    note = ""
    if (limit := config.seat_limit(a)) and count > limit:
        note = f"\n⚠️ Сотрудников уже {count}, а мест {limit}. Новых бот не пустит, лишних отключите через /remove ID."
    await msg.answer(f"Готово: «{a['name']}» — {plan_name(a['plan'])}, сотрудников {seats_text(a, count)}.{note}")
    if a["plan"]:
        for m in await db.agency_members(a["id"]):
            lang = m["lang"]
            until = t("until_date", lang).format(date=fmt_date(a["until"])) if a.get("until") else t("no_limit_date", lang)
            seats = plan_seats(config.seat_limit(a) or 0, lang).lower()
            try:
                await msg.bot.send_message(m["id"], t("plan_changed", lang).format(
                    name=a["name"], plan=plan_name(a["plan"], lang), seats=seats, until=until))
            except Exception:
                pass


@router.message(Command("move"))
async def move(msg: Message):
    """/move ID №А — перенести сотрудника в агентство."""
    if not admin(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await msg.answer("Как перенести: /move ID_сотрудника №агентства (например /move 123456789 3). Всё есть в /users.")
        return
    user, a = await db.get_user(int(parts[1])), await db.get_agency(int(parts[2]))
    if not user or not a:
        await msg.answer("Не нашёл сотрудника или агентство. Посмотрите в /users.")
        return
    old = user["agency_id"]
    await db.update_user(user["id"], agency_id=a["id"], authorized=1, trial_warned=0, pending=0)
    try:
        lang = user["lang"]
        await msg.bot.send_message(user["id"], t("joined", lang).format(name=a["name"]),
                                   reply_markup=main_kb(await db.get_user(user["id"])))
    except Exception:
        pass
    text = f"Готово: {user['name']} теперь в «{a['name']}»."
    if old and old != a["id"] and await db.delete_agency_if_empty(old):
        text += f" Пустое агентство №{old} удалено."
    count = len(await db.agency_members(a["id"]))
    if (limit := config.seat_limit(a)) and count > limit:
        text += f"\n⚠️ Сотрудников {count}, а по тарифу мест {limit}."
    await msg.answer(text)


@router.message(Command("rename"))
async def rename(msg: Message):
    if not admin(msg):
        return
    parts = (msg.text or "").split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit() or not (a := await db.get_agency(int(parts[1]))):
        await msg.answer("Как переименовать: /rename №А Название (например /rename 3 Baht Residence).")
        return
    await db.update_agency(a["id"], name=parts[2].strip())
    await msg.answer(f"Готово: агентство №{a['id']} теперь «{parts[2].strip()}».")


@router.message(Command("newagency"))
async def new_agency(msg: Message):
    if not admin(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await msg.answer("Как создать: /newagency Название. Срок пробный, тариф потом через /plan и /extend.")
        return
    until = (date.today() + timedelta(days=config.trial_days)).isoformat()
    a = await db.create_agency(parts[1].strip(), until)
    await msg.answer(f"Создано агентство №{a['id']} «{a['name']}», до {fmt_date(until)}.\n"
                     f"Код для сотрудников: {a['code']}")


@router.message(Command("remove"))
async def remove(msg: Message):
    """/remove ID — отключить сотрудника (освобождает место)."""
    if not admin(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or not (user := await db.get_user(int(parts[1]))):
        await msg.answer("Как отключить: /remove ID_сотрудника. ID есть в /users.")
        return
    await db.update_user(user["id"], authorized=0, agency_id=None)
    await msg.answer(f"Готово: {user['name']} отключён, место освободилось.")


# --- тарифы и оплата переводом на карту ---

def tariff_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn(t("tariff_btn", lang).format(level=t(f"level_{lvl}", lang), amount=money(config.price(lvl))), f"pay:{lvl}")]
        for lvl in LEVELS
    ])


def tariff_text(user: dict) -> str:
    lang = user["lang"]
    current = ""
    a = user.get("agency")
    if a and a.get("until") and not agency_over(a):
        current = t("tariff_current", lang).format(level=plan_name(a.get("plan"), lang), date=fmt_date(a["until"]))
    return t("tariff_title", lang).format(
        days=config.paid_days, lite=money(config.price_lite), standard=money(config.price_standard),
        pro=money(config.price_pro), current=current,
        lite_seats=plan_seats(config.lite_seats, lang), standard_seats=plan_seats(config.standard_seats, lang),
        pro_seats=plan_seats(config.pro_seats, lang))


async def send_tariffs(message: Message, user_id: int, name: str):
    user = await db.ensure_user(user_id, name)
    await message.answer(tariff_text(user), parse_mode="HTML", reply_markup=tariff_kb(user["lang"]))


@router.message(Command("tariff"))
@router.message(F.text.in_(menu_texts("menu_tariff")))
async def show_tariff(msg: Message):
    await send_tariffs(msg, msg.from_user.id, msg.from_user.full_name)


@router.callback_query(F.data == "tariff")
async def tariff_cb(cb: CallbackQuery):
    await send_tariffs(cb.message, cb.from_user.id, cb.from_user.full_name)
    await cb.answer()


@router.callback_query(F.data.startswith("pay:"))
async def choose_tariff(cb: CallbackQuery):
    level = cb.data.split(":")[1]
    if level not in LEVELS:
        await cb.answer()
        return
    user = await db.ensure_user(cb.from_user.id, cb.from_user.full_name)
    lang = user["lang"]
    await db.update_user(cb.from_user.id, pending_level=level)
    owner = f"\n{config.pay_card_owner}" if config.pay_card_owner else ""
    text = t("pay_info", lang).format(level=t(f"level_{level}", lang), amount=money(config.price(level)),
                                      days=config.paid_days, card=config.pay_card, owner=owner)
    rows = [[btn(t("paid_btn", lang), f"paid:{level}")], [btn(t("other_tariff_btn", lang), "tariff")]]
    if config.click_url:
        rows.insert(0, [InlineKeyboardButton(text=t("click_btn", lang), url=config.click_url)])
        text += t("click_info", lang).format(amount=money(config.price(level)))
        if config.click_ussd:
            ussd = config.click_ussd.format(amount=config.price(level))
            text += t("click_ussd", lang).format(ussd=ussd)
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("paid:"))
async def i_paid(cb: CallbackQuery):
    level = cb.data.split(":")[1]
    if level not in LEVELS:
        await cb.answer()
        return
    user = await db.ensure_user(cb.from_user.id, cb.from_user.full_name)
    await db.update_user(cb.from_user.id, pending_level=level)
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer(t("pay_sent", user["lang"]))
    uname = f" (@{cb.from_user.username})" if cb.from_user.username else ""
    text = (f"💳 Оплата на проверку\n{user['name']}{uname}, id {user['id']}\n"
            f"Тариф: {t(f'level_{level}', 'ru')}, {money(config.price(level))} сум\n"
            + (f"Агентство: «{user['agency']['name']}» №{user['agency']['id']}, сейчас "
               f"{plan_name(user['agency']['plan'])}"
               + (f", до {fmt_date(user['agency']['until'])}" if user['agency'].get("until") else "")
               if user.get("agency") else "Агентства пока нет, после подтверждения создам новое")
            + "\n\nПроверьте поступление на карту и нажмите кнопку.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("✅ Подтвердить", f"payok:{user['id']}:{level}"),
                                                btn("❌ Отклонить", f"payno:{user['id']}:{level}")]])
    for admin_id in config.admin_ids:
        try:
            await cb.bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            pass
    await cb.answer()


@router.callback_query(F.data.startswith("payok:") | F.data.startswith("payno:"))
async def admin_decision(cb: CallbackQuery):
    if cb.from_user.id not in config.admin_ids:
        await cb.answer()
        return
    action, uid, level = cb.data.split(":")
    user = await db.get_user(int(uid))
    if not user or level not in LEVELS:
        await cb.answer("Пользователь не найден", show_alert=True)
        return
    lang = user["lang"]
    username = None
    try:
        chat = await cb.bot.get_chat(user["id"])
        username = chat.username
    except Exception:
        pass
    if action == "payok":
        agency = user.get("agency")
        if not agency:  # оплатил без кода: заводим ему агентство
            agency = await db.create_agency(user["name"], None)
        until = new_until(agency)
        await db.update_agency(agency["id"], plan=level, until=until, warned=0)
        await db.update_user(user["id"], authorized=1, active=1, pending=0, trial_warned=0,
                             pending_level=None, agency_id=agency["id"])
        if level == "lite":
            await trim_lite_districts(agency["id"])
        else:
            for m in await db.agency_members(agency["id"]):
                await db.update_user(m["id"], last_digest=None)
        user = await db.get_user(user["id"])
        text = t("pay_confirmed", lang).format(level=t(f"level_{level}", lang), date=fmt_date(until))
        if level == "lite":
            text += t("pay_confirmed_lite", lang)
        try:
            await cb.bot.send_message(user["id"], text, reply_markup=main_kb(user))
            if not agency.get("plan") and agency.get("code"):
                await cb.bot.send_message(user["id"], t("team_code", lang).format(code=user["agency"]["code"]))
        except Exception:
            pass
        # остальным сотрудникам — что тариф агентства сменился
        for m in await db.agency_members(agency["id"]):
            if m["id"] == user["id"]:
                continue
            ml = m["lang"]
            try:
                await cb.bot.send_message(m["id"], t("plan_changed", ml).format(
                    name=agency["name"], plan=t(f"level_{level}", ml),
                    seats=plan_seats(config.seat_limit(user["agency"]) or 0, ml).lower(),
                    until=t("until_date", ml).format(date=fmt_date(until))))
            except Exception:
                pass
        saved = await log_payment(user, level, "оплачен", until, username)
        result = f"✅ Подтверждено: «{user['agency']['name']}» — {t(f'level_{level}', 'ru')} до {fmt_date(until)}" + ("" if saved else " (в таблицу не записалось)")
    else:
        await db.update_user(user["id"], pending_level=None)
        try:
            await cb.bot.send_message(user["id"], t("pay_rejected", lang).format(contact=contact_suffix()))
        except Exception:
            pass
        await log_payment(user, level, "отклонён", None, username)
        result = "❌ Отклонено"
    try:
        await cb.message.edit_text(f"{cb.message.text}\n\n{result}", reply_markup=None)
    except Exception:
        pass
    await cb.answer(result[:200])


@router.message(Command("level"))
async def set_level(msg: Message):
    """/level ID lite|standard|pro — старая команда: меняет тариф агентства этого сотрудника."""
    if msg.from_user.id not in config.admin_ids:
        return
    parts = (msg.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or parts[2] not in LEVELS:
        await msg.answer("Как сменить тариф: /plan №А lite|standard|pro. № агентства есть в /users.")
        return
    a = await find_agency(parts[1])
    if not a:
        await msg.answer("Нет такого агентства. Посмотрите № в /users.")
        return
    await db.update_agency(a["id"], plan=parts[2])
    if parts[2] == "lite":
        await trim_lite_districts(a["id"])
    await msg.answer(f"Готово: «{a['name']}» — {t(f'level_{parts[2]}', 'ru')}.")


@router.message(Command("msg"))
async def send_to_user(msg: Message):
    """/msg ID текст — написать человеку от имени бота."""
    if not admin(msg):
        return
    parts = (msg.text or "").split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await msg.answer("Как написать человеку от имени бота: /msg ID текст "
                         "(например /msg 123456789 Здравствуйте!). ID есть в /users.")
        return
    try:
        await msg.bot.send_message(int(parts[1]), parts[2])
    except Exception as e:
        await msg.answer(f"Не отправилось: {e}")
        return
    await msg.answer("✅ Отправлено.")


@router.message(F.text & ~F.text.startswith("/"))
async def forward_to_admins(msg: Message):
    """Обычный текст, который боту не команда, пересылаем админам, чтобы ответить через /msg."""
    if admin(msg):
        return
    user = await db.get_user(msg.from_user.id)
    who = msg.from_user.full_name + (f" (@{msg.from_user.username})" if msg.from_user.username else "")
    if user and user.get("agency_id") and (a := await db.get_agency(user["agency_id"])):
        who += f", агентство «{a['name']}» №{a['id']}"
    from .scheduler import notify_admins
    await notify_admins(msg.bot, f"💬 Сообщение боту от {who}, id {msg.from_user.id}:\n{msg.text}\n\n"
                                 f"Ответить: /msg {msg.from_user.id} текст")
