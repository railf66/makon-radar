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
    # 1 = пробный период по коду с визитки включается только после одобрения админом
    trial_approval: bool = os.getenv("TRIAL_APPROVAL", "1") == "1"
    # Сколько сотрудников входит в тариф агентства. 0 = без ограничения.
    # Сверх этого админ добавляет платные места: /plan №А lite 1
    trial_seats: int = int(os.getenv("TRIAL_SEATS", "0"))
    lite_seats: int = int(os.getenv("LITE_SEATS", "2"))
    standard_seats: int = int(os.getenv("STANDARD_SEATS", "5"))
    pro_seats: int = int(os.getenv("PRO_SEATS", "10"))
    # Кому писать, чтобы продолжить после пробного периода (например @username или телефон)
    contact: str = os.getenv("CONTACT", "")
    olx_enabled: bool = os.getenv("OLX_ENABLED", "1") == "1"
    poll_interval: int = int(os.getenv("POLL_INTERVAL", "600"))
    fresh_hours: int = int(os.getenv("FRESH_HOURS", "48"))
    uzs_per_usd: float = float(os.getenv("UZS_PER_USD", "12800"))
    db_path: str = os.getenv("DB_PATH", "data/bot.db")
    # Ссылка на вебхук Make для секретаря Дильнозы (пусто = кнопки «Дильнозе» нет)
    dilnoza_webhook: str = os.getenv("DILNOZA_WEBHOOK", "")
    # Кто видит кнопку «Дильнозе»: Telegram id через запятую (пусто = только админы)
    dilnoza_users: set[int] = field(default_factory=lambda: {
        int(x) for x in os.getenv("DILNOZA_USERS", "").split(",") if x.strip().isdigit()
    })

    # Как часто проверять, не сняты ли с OLX объекты Дильнозы, в часах
    dilnoza_check_hours: int = int(os.getenv("DILNOZA_CHECK_HOURS", "24"))

    # --- Тарифы Makon Radar и оплата переводом на карту ---
    price_lite: int = int(os.getenv("PRICE_LITE", "150000"))
    price_standard: int = int(os.getenv("PRICE_STANDARD", "300000"))
    price_pro: int = int(os.getenv("PRICE_PRO", "500000"))
    pay_card: str = os.getenv("PAY_CARD", "")
    pay_card_owner: str = os.getenv("PAY_CARD_OWNER", "")
    paid_days: int = int(os.getenv("PAID_DAYS", "30"))
    # За сколько дней до конца срока напоминать об оплате
    warn_days: int = int(os.getenv("WARN_DAYS", "3"))
    # Лайт: сколько районов можно выбрать и как часто присылать подборку (минуты)
    lite_max_districts: int = int(os.getenv("LITE_MAX_DISTRICTS", "3"))
    lite_digest_minutes: int = int(os.getenv("LITE_DIGEST_MIN", "60"))
    # Вебхук Make, который записывает оплаты в таблицу «Makon Radar — подписчики»
    subs_webhook: str = os.getenv("SUBS_WEBHOOK", "")

    def seats(self, level: str | None) -> int:
        """Мест по тарифу (без доп. мест). 0 = без ограничения. None = пробный период."""
        return {"lite": self.lite_seats, "standard": self.standard_seats, "pro": self.pro_seats}.get(level, self.trial_seats)

    def seat_limit(self, agency: dict) -> int | None:
        """Сколько сотрудников можно в агентстве; None = без ограничения."""
        base = self.seats(agency.get("plan"))
        return None if base == 0 else base + (agency.get("extra_seats") or 0)

    def price(self, level: str) -> int:
        return {"lite": self.price_lite, "standard": self.price_standard, "pro": self.price_pro}[level]

    def can_dilnoza(self, user_id: int) -> bool:
        return bool(self.dilnoza_webhook) and user_id in (self.dilnoza_users or self.admin_ids)


config = Config()

LEVELS = ("lite", "standard", "pro")

# Разделы OLX.uz, которые собираем (id сверены с olx.uz 2026-10-27).
OLX_BASE = "https://www.olx.uz"
OLX_SECTIONS = [
    # deal: sale | rent, ptype: flat | house | commercial
    {"deal": "sale", "ptype": "flat", "path": "nedvizhimost/kvartiry/prodazha", "category_id": 13},
    {"deal": "rent", "ptype": "flat", "path": "nedvizhimost/kvartiry/arenda-dolgosrochnaya", "category_id": 1147},
    {"deal": "sale", "ptype": "house", "path": "nedvizhimost/doma/prodazha", "category_id": 18},
    {"deal": "rent", "ptype": "house", "path": "nedvizhimost/doma/arenda-dolgosrochnaya", "category_id": 330},
    {"deal": "sale", "ptype": "commercial", "path": "nedvizhimost/kommercheskie-pomeshcheniya/prodazha", "category_id": 14},
    {"deal": "rent", "ptype": "commercial", "path": "nedvizhimost/kommercheskie-pomeshcheniya/arenda", "category_id": 11},
]
# Ташкент на OLX.uz
OLX_CITY_SLUG = "tashkent"
OLX_REGION_ID = 5
OLX_CITY_ID = 4
