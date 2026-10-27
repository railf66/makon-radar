import json
import os
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
        await self.conn.commit()

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

    async def active_users(self):
        cur = await self.conn.execute("SELECT id FROM users WHERE authorized=1 AND active=1")
        return [await self.get_user(r["id"]) for r in await cur.fetchall()]

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
        return {"users": users[0], "listings": listings[0], "sent": sent[0]}


db = DB()
