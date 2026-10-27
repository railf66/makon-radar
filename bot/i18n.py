# Тексты бота на русском и узбекском (латиница).

# Районы Ташкента: ключ -> (ru, uz, варианты написания для поиска в объявлении)
DISTRICTS = {
    "almazar": ("Алмазарский", "Olmazor", ["алмазар", "olmazor", "almazar"]),
    "bektemir": ("Бектемирский", "Bektemir", ["бектемир", "bektemir"]),
    "mirabad": ("Мирабадский", "Mirobod", ["мирабад", "mirobod", "mirabad"]),
    "mirzo": ("Мирзо-Улугбекский", "Mirzo Ulug'bek", ["улугбек", "ulug'bek", "ulugbek", "ulug‘bek"]),
    "sergeli": ("Сергелийский", "Sergeli", ["сергели", "sergeli"]),
    "uchtepa": ("Учтепинский", "Uchtepa", ["учтеп", "uchtepa"]),
    "chilanzar": ("Чиланзарский", "Chilonzor", ["чиланзар", "chilonzor", "chilanzar"]),
    "shaykhantahur": ("Шайхантахурский", "Shayxontohur", ["шайхантах", "shayxontohur", "shaykhantakhur"]),
    "yunusabad": ("Юнусабадский", "Yunusobod", ["юнусабад", "yunusobod", "yunusabad"]),
    "yakkasaray": ("Яккасарайский", "Yakkasaroy", ["яккасар", "yakkasaroy", "yakkasaray"]),
    "yashnabad": ("Яшнабадский", "Yashnobod", ["яшнабад", "yashnobod", "yashnabad"]),
    "yangihayot": ("Янгихаётский", "Yangihayot", ["янгихаёт", "янгихает", "yangihayot"]),
}

T = {
    "choose_lang": {"ru": "Выберите язык / Tilni tanlang", "uz": "Tilni tanlang / Выберите язык"},
    "need_code": {
        "ru": "Это пилотная версия бота для агентства. Введите код доступа:",
        "uz": "Bu agentlik uchun botning sinov versiyasi. Kirish kodini kiriting:",
    },
    "bad_code": {"ru": "Неверный код. Попробуйте ещё раз.", "uz": "Kod noto‘g‘ri. Qayta urinib ko‘ring."},
    "pilot_over": {
        "ru": "Пилотный период закончился. Свяжитесь с нами, чтобы продолжить.",
        "uz": "Sinov muddati tugadi. Davom ettirish uchun biz bilan bog‘laning.",
    },
    "welcome": {
        "ru": "Здравствуйте! Я присылаю новые объявления о недвижимости в Ташкенте с OLX.uz сразу после публикации.\n\nНастройте фильтры, и я начну присылать подходящие варианты.",
        "uz": "Assalomu alaykum! Men OLX.uz dagi Toshkent ko‘chmas mulk e’lonlarini joylangan zahoti yuboraman.\n\nFiltrlarni sozlang va men mos variantlarni yubora boshlayman.",
    },
    "menu_filters": {"ru": "⚙️ Фильтры", "uz": "⚙️ Filtrlar"},
    "menu_latest": {"ru": "🆕 Последние объявления", "uz": "🆕 So‘nggi e’lonlar"},
    "menu_export": {"ru": "📊 Выгрузка в Excel", "uz": "📊 Excelga yuklash"},
    "menu_pause": {"ru": "⏸ Пауза", "uz": "⏸ To‘xtatish"},
    "menu_resume": {"ru": "▶️ Включить рассылку", "uz": "▶️ Yuborishni yoqish"},
    "menu_lang": {"ru": "🌐 Язык", "uz": "🌐 Til"},
    "paused": {"ru": "Рассылка на паузе.", "uz": "Yuborish to‘xtatildi."},
    "resumed": {"ru": "Рассылка включена.", "uz": "Yuborish yoqildi."},
    "filters_title": {"ru": "Ваши фильтры. Нажмите, чтобы изменить:", "uz": "Filtrlaringiz. O‘zgartirish uchun bosing:"},
    "f_deal": {"ru": "Сделка", "uz": "Bitim"},
    "f_ptype": {"ru": "Тип", "uz": "Turi"},
    "f_rooms": {"ru": "Комнаты", "uz": "Xonalar"},
    "f_price": {"ru": "Цена, $", "uz": "Narx, $"},
    "f_districts": {"ru": "Районы", "uz": "Tumanlar"},
    "f_owner": {"ru": "Только собственники", "uz": "Faqat egasidan"},
    "done": {"ru": "✅ Готово", "uz": "✅ Tayyor"},
    "back": {"ru": "⬅️ Назад", "uz": "⬅️ Orqaga"},
    "any": {"ru": "любые", "uz": "har qanday"},
    "yes": {"ru": "да", "uz": "ha"},
    "no": {"ru": "нет", "uz": "yo‘q"},
    "deal_sale": {"ru": "Продажа", "uz": "Sotuv"},
    "deal_rent": {"ru": "Аренда", "uz": "Ijara"},
    "ptype_flat": {"ru": "Квартира", "uz": "Kvartira"},
    "ptype_house": {"ru": "Дом", "uz": "Hovli/uy"},
    "ptype_commercial": {"ru": "Коммерция", "uz": "Tijorat"},
    "price_ask": {
        "ru": "Отправьте диапазон цены в долларах, например: 30000-60000\nДля аренды в месяц: 300-600\nОтправьте 0, чтобы убрать ограничение.",
        "uz": "Narx oralig‘ini dollarda yuboring, masalan: 30000-60000\nIjara uchun oyiga: 300-600\nCheklovni olib tashlash uchun 0 yuboring.",
    },
    "price_bad": {"ru": "Не понял. Пример: 30000-60000", "uz": "Tushunmadim. Misol: 30000-60000"},
    "saved": {"ru": "Сохранено.", "uz": "Saqlandi."},
    "no_results": {"ru": "Пока нет подходящих объявлений.", "uz": "Hozircha mos e’lonlar yo‘q."},
    "owner": {"ru": "👤 Собственник", "uz": "👤 Egasidan"},
    "agent": {"ru": "🏢 Посредник/агентство", "uz": "🏢 Vositachi/agentlik"},
    "rooms_word": {"ru": "комн.", "uz": "xona"},
    "area_word": {"ru": "м²", "uz": "m²"},
    "floor_word": {"ru": "этаж", "uz": "qavat"},
    "open": {"ru": "Открыть на OLX", "uz": "OLX da ochish"},
    "export_caption": {
        "ru": "Объявления за 7 дней по вашим фильтрам",
        "uz": "Filtrlaringiz bo‘yicha 7 kunlik e’lonlar",
    },
}


def t(key: str, lang: str) -> str:
    return T[key].get(lang) or T[key]["ru"]


def district_name(key: str, lang: str) -> str:
    ru, uz, _ = DISTRICTS[key]
    return uz if lang == "uz" else ru
