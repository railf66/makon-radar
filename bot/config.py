import os
from dataclasses import dataclass, field
from datetime import date


def _load_env(path: str = ".env") -> None:
    """Простая загрузка .env без лишних зависимостей."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env()


@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: set[int] = field(default_factory=lambda: {
        int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
    })
    access_code: str = os.getenv("ACCESS_CODE", "")
    pilot_until: date | None = (
        date.fromisoformat(os.environ["PILOT_UNTIL"]) if os.getenv("PILOT_UNTIL") else None
    )
    # Пробный период для каждого агента: столько дней с момента ввода кода
    trial_days: int = int(os.getenv("TRIAL_DAYS", "14"))
    # Кому писать, чтобы продолжить после пробного периода (например @username или телефон)
    contact: str = os.getenv("CONTACT", "")
    olx_enabled: bool = os.getenv("OLX_ENABLED", "1") == "1"
    poll_interval: int = int(os.getenv("POLL_INTERVAL", "600"))
    fresh_hours: int = int(os.getenv("FRESH_HOURS", "48"))
    uzs_per_usd: float = float(os.getenv("UZS_PER_USD", "12800"))
    db_path: str = os.getenv("DB_PATH", "data/bot.db")


config = Config()

# Разделы OLX.uz, которые собираем (id сверены с olx.uz 2026-10-27).
# Коммерция выключена по решению агентства: category_id 14 (продажа) и 11 (аренда).
OLX_BASE = "https://www.olx.uz"
OLX_SECTIONS = [
    # deal: sale | rent, ptype: flat | house | commercial
    {"deal": "sale", "ptype": "flat", "path": "nedvizhimost/kvartiry/prodazha", "category_id": 13},
    {"deal": "rent", "ptype": "flat", "path": "nedvizhimost/kvartiry/arenda-dolgosrochnaya", "category_id": 1147},
    {"deal": "sale", "ptype": "house", "path": "nedvizhimost/doma/prodazha", "category_id": 18},
    {"deal": "rent", "ptype": "house", "path": "nedvizhimost/doma/arenda-dolgosrochnaya", "category_id": 330},
]
# Ташкент на OLX.uz
OLX_CITY_SLUG = "tashkent"
OLX_REGION_ID = 5
OLX_CITY_ID = 4
