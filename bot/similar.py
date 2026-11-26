"""Поиск похожих агентств и людей, чтобы замечать повторные заявки на пробный период
(например «RizoMulk 22» с нового Telegram, когда «RizoMulk» уже пробовал)."""
import re
from difflib import SequenceMatcher

# Кириллица → латиница, чтобы «РизоМулк» и «RizoMulk» считались одним названием
_TR = dict(zip("абвгдезийклмнопрстуфхцыэ", "abvgdeziyklmnoprstufxcye"))
_TR.update({"ё": "yo", "ж": "j", "ч": "ch", "ш": "sh", "щ": "sh", "ю": "yu", "я": "ya",
            "ъ": "", "ь": "", "қ": "q", "ғ": "g", "ҳ": "h", "ў": "o"})

# Общие слова, по которым агентства совпадать не должны
GENERIC = {
    "real", "estate", "realty", "realestate", "group", "groups", "home", "homes", "house", "uy", "uylar",
    "agency", "agentstvo", "nedvijimost", "rieltor", "rieltory", "realtor", "realtors", "invest",
    "city", "tashkent", "toshkent", "uz", "uzb", "uzbekistan", "llc", "ooo", "mchj", "company",
    "service", "servis", "pro", "plus", "new", "best", "top", "official", "makon", "kvartira",
    "kvartiry", "arenda", "ijara", "sotuv", "prodaja", "broker", "brokers", "property", "the",
}


def _translit(s: str) -> str:
    return "".join(_TR.get(ch, ch) for ch in s.lower())


def tokens(name: str | None) -> list[str]:
    words = re.findall(r"[a-z]+", _translit(name or "").replace("'", "").replace("‘", "").replace("ʻ", ""))
    return [w for w in words if len(w) >= 3 and w not in GENERIC]


def similar(a: str | None, b: str | None, strict: bool = False) -> bool:
    """strict — для имён людей: только почти полное совпадение, без общего слова
    (иначе одинаковые фамилии давали бы ложные совпадения)."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    ca, cb = "".join(ta), "".join(tb)
    if ca == cb:
        return True
    if strict:
        return min(len(ca), len(cb)) >= 5 and SequenceMatcher(None, ca, cb).ratio() >= 0.9
    short, long_ = sorted((ca, cb), key=len)
    if len(short) >= 5 and short in long_:
        return True
    if min(len(ca), len(cb)) >= 5 and SequenceMatcher(None, ca, cb).ratio() >= 0.85:
        return True
    # Общее отличительное слово длиной от 5 букв (RizoMulk Group ↔ RizoMulk 22)
    return any(len(w) >= 5 and w in tb for w in ta)
