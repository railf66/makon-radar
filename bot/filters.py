from html import escape

from .i18n import t


def matches(item: dict, f: dict) -> bool:
    if f["deal"] and item["deal"] not in f["deal"]:
        return False
    if f["ptype"] and item["ptype"] not in f["ptype"]:
        return False
    if f["rooms"]:
        r = item.get("rooms")
        if r is None:
            return False
        if min(r, 4) not in f["rooms"]:
            return False
    price = item.get("price_usd")
    if f["price_min"] and (price is None or price < f["price_min"]):
        return False
    if f["price_max"] and (price is None or price > f["price_max"]):
        return False
    if f["districts"] and item.get("district") not in f["districts"]:
        return False
    if f["owner_only"] and not item.get("is_owner"):
        return False
    return True


def format_listing(item: dict, lang: str) -> str:
    deal = t(f"deal_{item['deal']}", lang)
    ptype = t(f"ptype_{item['ptype']}", lang)
    lines = [f"<b>{deal} · {ptype}</b>", escape(item["title"])]
    details = []
    if item.get("rooms"):
        details.append(f"{item['rooms']} {t('rooms_word', lang)}")
    if item.get("area"):
        details.append(f"{item['area']:g} {t('area_word', lang)}")
    if item.get("floor"):
        details.append(f"{t('floor_word', lang)} {item['floor']}")
    if details:
        lines.append(" · ".join(details))
    if item.get("price_text"):
        lines.append(f"💰 {escape(item['price_text'])}")
    if item.get("district_raw"):
        lines.append(f"📍 {escape(item['district_raw'])}")
    lines.append(t("owner", lang) if item.get("is_owner") else t("agent", lang))
    return "\n".join(lines)
