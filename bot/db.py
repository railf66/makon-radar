import json
import os
import random
from datetime import datetime, timedelta, timezone

import aiosqlite

from .config import config

DEFAULT_FILTERS = {
    "deal": [],        # [] = любые; иначе ["sale", "rent"]
    "ptype": [],       # ["flat", "house", "commercial"]
    "rooms": [],       # [1, 2, 3, 4] (4 = 4 и больше)
    "price_min": 0,    # USD, 0 = без ограничения
    "price_max": 0,
    "districts": [],   # ключи из i18n.DISTRICTS
    "owner_only": False,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    lang TEXT DEFAULT 'ru',
    authorized INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    filters TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS agencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    plan TEXT DEFAULT 'trial',      -- trial | light | pro
    extra_seats INTEGER DEFAULT 0,  -- докупленные места сверх тарифа
    until TEXT,                     -- последний день доступа, NULL = без срока
    warned INTEGER DEFAULT 0,       -- 0 — нет, 1 — предупредили за день, 2 — срок вышел
    code TEXT UNIQUE,               -- код, по которому сотрудники входят в агентство
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    deal TEXT, ptype TEXT,
    title TEXT, url TEXT,
    price_usd REAL, price_text TEXT,
    rooms INTEGER, area REAL, floor TEXT,
    district TEXT, district_raw TEXT,
    is_owner INTEGER,
    photo TEXT,
    created_at TEXT,
    first_seen TEXT
);
CREATE INDEX IF NOT EXISTS idx_listings_seen ON listings(first_seen);
CREATE TABLE IF NOT EXISTS dilnoza (
    listing_id TEXT PRIMARY KEY,
    title TEXT, url TEXT,
    added_at TEXT,
    removed_at TEXT
);
CREATE TABLE IF NOT EXISTS sent (
    user_id INTEGER, listing_id TEXT,
    PRIMARY KEY (user_id, listing_id)
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DB:
    def __init__(self, path: str = config.db_path):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self._migrate()
        await self.conn.commit()

    async def _migrate(self):
        cols = {r[1] for r in await (await self.conn.execute("PRAGMA table_info(users)")).fetchall()}
        if "trial_until" not in cols:
            await self.conn.execute("ALTER TABLE users ADD COLUMN trial_until TEXT")
            # Кто подключился до личных сроков, получает общий срок пилота (PILOT_UNTIL)
            if config.pilot_until:
                await self.conn.execute("UPDATE users SET trial_until=? WHERE authorized=1",
                                        (config.pilot_until.isoformat(),))
        if "trial_warned" not in cols:
            # 0 — не предупреждали, 1 — предупредили за день, 2 — сообщили, что срок вышел
            await self.conn.execute("ALTER TABLE users ADD COLUMN trial_warned INTEGER DEFAULT 0")
        if "pending" not in cols:
            # 1 — ввёл код с визитки и ждёт одобрения пробного периода админом
            await self.conn.execute("ALTER TABLE users ADD COLUMN pending INTEGER DEFAULT 0")
        if "agency_id" not in cols:
            await self.conn.execute("ALTER TABLE users ADD COLUMN agency_id INTEGER")
        # Агенты, подключившиеся до агентств: каждый получает своё агентство с прежним сроком,
        # потом админ объединяет сотрудников командой /move
        cur = await self.conn.execute(
            "SELECT * FROM users WHERE authorized=1 AND agency_id IS NULL ORDER BY created_at")
        for u in await cur.fetchall():
            if u["id"] in config.admin_ids:
                continue
            agency_id = await self._insert_agency(u["name"], u["trial_until"], u["trial_warned"] or 0)
            await self.conn.execute("UPDATE users SET agency_id=? WHERE id=?", (agency_id, u["id"]))

    async def close(self):
        if self.conn:
            await self.conn.close()

    # --- пользователи ---
    async def get_user(self, user_id: int):
        cur = await self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return None
        user = dict(row)
        user["filters"] = {**DEFAULT_FILTERS, **json.loads(user["filters"] or "{}")}
        user["agency"] = await self.get_agency(user["agency_id"]) if user.get("agency_id") else None
        return user

    async def ensure_user(self, user_id: int, name: str):
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (id, name, filters, created_at) VALUES (?,?,?,?)",
            (user_id, name, json.dumps(DEFAULT_FILTERS), now()),
        )
        await self.conn.commit()
        return await self.get_user(user_id)

    async def update_user(self, user_id: int, **fields):
        if "filters" in fields:
            fields["filters"] = json.dumps(fields["filters"])
        sets = ", ".join(f"{k}=?" for k in fields)
        await self.conn.execute(f"UPDATE users SET {sets} WHERE id=?", (*fields.values(), user_id))
        await self.conn.commit()

    async def authorized_users(self):
        cur = await self.conn.execute("SELECT id FROM users WHERE authorized=1 ORDER BY created_at")
        return [await self.get_user(r["id"]) for r in await cur.fetchall()]

    async def active_users(self):
        cur = await self.conn.execute("SELECT id FROM users WHERE authorized=1 AND active=1")
        return [await self.get_user(r["id"]) for r in await cur.fetchall()]

    # --- агентства ---
    async def _new_code(self) -> str:
        """Короткий код из цифр, его удобно набрать на телефоне."""
        while True:
            code = str(random.randint(100000, 999999))
            cur = await self.conn.execute("SELECT 1 FROM agencies WHERE code=?", (code,))
            if not await cur.fetchone():
                return code

    async def _insert_agency(self, name: str, until: str | None, warned: int = 0) -> int:
        cur = await self.conn.execute(
            "INSERT INTO agencies (name, until, warned, code, created_at) VALUES (?,?,?,?,?)",
            (name, until, warned, await self._new_code(), now()),
        )
        return cur.lastrowid

    async def create_agency(self, name: str, until: str | None) -> dict:
        agency_id = await self._insert_agency(name, until)
        await self.conn.commit()
        return await self.get_agency(agency_id)

    async def get_agency(self, agency_id: int):
        cur = await self.conn.execute("SELECT * FROM agencies WHERE id=?", (agency_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def agency_by_code(self, code: str):
        cur = await self.conn.execute("SELECT * FROM agencies WHERE code=?", (code.strip(),))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def update_agency(self, agency_id: int, **fields):
        sets = ", ".join(f"{k}=?" for k in fields)
        await self.conn.execute(f"UPDATE agencies SET {sets} WHERE id=?", (*fields.values(), agency_id))
        await self.conn.commit()

    async def agencies(self):
        cur = await self.conn.execute("SELECT * FROM agencies ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]

    async def agency_members(self, agency_id: int):
        cur = await self.conn.execute(
            "SELECT id FROM users WHERE agency_id=? AND authorized=1 ORDER BY created_at", (agency_id,))
        return [await self.get_user(r["id"]) for r in await cur.fetchall()]

    async def delete_agency_if_empty(self, agency_id: int) -> bool:
        if await self.agency_members(agency_id):
            return False
        await self.conn.execute("DELETE FROM agencies WHERE id=?", (agency_id,))
        await self.conn.commit()
        return True

    # --- объявления ---
    async def add_listing(self, item: dict) -> bool:
        """Сохраняет объявление. True, если оно новое."""
        cur = await self.conn.execute(
            """INSERT OR IGNORE INTO listings
            (id, deal, ptype, title, url, price_usd, price_text, rooms, area, floor,
             district, district_raw, is_owner, photo, created_at, first_seen)
            VALUES (:id,:deal,:ptype,:title,:url,:price_usd,:price_text,:rooms,:area,:floor,
                    :district,:district_raw,:is_owner,:photo,:created_at,:first_seen)""",
            {**item, "first_seen": now()},
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def get_listing(self, listing_id: str):
        cur = await self.conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    # --- объекты у Дильнозы ---
    async def add_dilnoza(self, item: dict):
        await self.conn.execute(
            "INSERT OR REPLACE INTO dilnoza (listing_id, title, url, added_at, removed_at) VALUES (?,?,?,?,NULL)",
            (item["id"], item["title"], item["url"], now()),
        )
        await self.conn.commit()

    async def dilnoza_active(self):
        cur = await self.conn.execute("SELECT * FROM dilnoza WHERE removed_at IS NULL ORDER BY added_at")
        return [dict(r) for r in await cur.fetchall()]

    async def dilnoza_removed(self, listing_id: str):
        await self.conn.execute("UPDATE dilnoza SET removed_at=? WHERE listing_id=?", (now(), listing_id))
        await self.conn.commit()

    async def recent_listings(self, days: int = 7, limit: int = 2000):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        cur = await self.conn.execute(
            "SELECT * FROM listings WHERE first_seen>=? ORDER BY first_seen DESC LIMIT ?",
            (since, limit),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def mark_sent(self, user_id: int, listing_id: str) -> bool:
        cur = await self.conn.execute(
            "INSERT OR IGNORE INTO sent (user_id, listing_id) VALUES (?,?)", (user_id, listing_id)
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def stats(self):
        q = lambda sql: self.conn.execute(sql)
        users = await (await q("SELECT COUNT(*) FROM users WHERE authorized=1")).fetchone()
        listings = await (await q("SELECT COUNT(*) FROM listings")).fetchone()
        sent = await (await q("SELECT COUNT(*) FROM sent")).fetchone()
        agencies = await (await q("SELECT COUNT(*) FROM agencies")).fetchone()
        return {"users": users[0], "listings": listings[0], "sent": sent[0], "agencies": agencies[0]}


db = DB()
