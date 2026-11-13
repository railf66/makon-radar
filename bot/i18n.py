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
        "ru": "Введите код доступа с визитки или код вашего агентства (его даёт коллега). Нет кода? Выберите тариф кнопкой ниже.",
        "uz": "Vizitkadagi kirish kodini yoki agentligingiz kodini kiriting (uni hamkasbingiz beradi). Kod yo‘qmi? Quyidagi tugma orqali tarifni tanlang.",
    },
    "bad_code": {"ru": "Неверный код. Попробуйте ещё раз.", "uz": "Kod noto‘g‘ri. Qayta urinib ko‘ring."},
    "code_first": {
        "ru": "Сначала введите код доступа с визитки (обычным сообщением, без /).",
        "uz": "Avval vizitkadagi kirish kodini kiriting (oddiy xabar bilan, / belgisisiz).",
    },
    "trial_started": {
        "ru": "Код принят! Бесплатный пробный период до {date} включительно.",
        "uz": "Kod qabul qilindi! Bepul sinov muddati {date} gacha (shu kun ham kiradi).",
    },
    "team_code": {
        "ru": "Чтобы подключить коллег из вашего агентства, дайте им код {code}. Его вводят вместо кода с визитки.",
        "uz": "Agentligingizdagi hamkasblarni ulash uchun ularga {code} kodini bering. Uni vizitkadagi kod o‘rniga kiritishadi.",
    },
    "trial_pending": {
        "ru": "Код принят! Заявка на пробный период отправлена, мы подтвердим её в ближайшее время и бот вам напишет.",
        "uz": "Kod qabul qilindi! Sinov muddatiga ariza yuborildi, tez orada tasdiqlaymiz va bot sizga yozadi.",
    },
    "trial_rejected": {
        "ru": "Пробный период не подтверждён. Если вы из уже подключённого агентства, попросите у коллег код агентства.",
        "uz": "Sinov muddati tasdiqlanmadi. Agar agentligingiz allaqachon ulangan bo‘lsa, hamkasblardan agentlik kodini so‘rang.",
    },
    "joined": {
        "ru": "Вы подключены к агентству «{name}».",
        "uz": "Siz «{name}» agentligiga ulandingiz.",
    },
    "seats_full": {
        "ru": "В агентстве «{name}» заняты все места по тарифу ({limit}). Чтобы добавить сотрудника, свяжитесь с нами{contact}.",
        "uz": "«{name}» agentligida tarif bo‘yicha barcha o‘rinlar band ({limit}). Xodim qo‘shish uchun biz bilan bog‘laning{contact}.",
    },
    "team_info": {
        "ru": "🏢 {name}\nТариф: {plan}\nСотрудников: {count} из {limit}\nДоступ: {until}\nКод для коллег: {code}\n\n{members}",
        "uz": "🏢 {name}\nTarif: {plan}\nXodimlar: {count} / {limit}\nKirish: {until}\nHamkasblar uchun kod: {code}\n\n{members}",
    },
    "no_team": {"ru": "Вы не состоите в агентстве.", "uz": "Siz agentlikka a’zo emassiz."},
    "unlimited": {"ru": "без ограничения", "uz": "cheklanmagan"},
    "until_date": {"ru": "до {date} включительно", "uz": "{date} gacha"},
    "no_limit_date": {"ru": "без срока", "uz": "muddatsiz"},
    "plan_seats": {"ru": "До {n} сотрудников", "uz": "{n} tagacha xodim"},
    "plan_unlimited": {"ru": "Сотрудников без ограничения", "uz": "Xodimlar soni cheklanmagan"},
    "plan_extra": {"ru": "Дополнительный сотрудник сверх тарифа", "uz": "Tarifdan tashqari qo‘shimcha xodim"},
    "plan_changed": {
        "ru": "Ваше агентство «{name}» переведено на тариф {plan}: {seats}. Доступ {until}.",
        "uz": "«{name}» agentligingiz {plan} tarifiga o‘tkazildi: {seats}. Kirish {until}.",
    },
    "menu_team": {"ru": "👥 Моя команда", "uz": "👥 Jamoam"},
    "trial_tomorrow": {
        "ru": "Завтра, {date}, заканчивается доступ вашего агентства к Makon Radar. Чтобы продолжить получать объявления, свяжитесь с нами{contact}.",
        "uz": "Ertaga, {date}, agentligingizning Makon Radar’dan foydalanish muddati tugaydi. E’lonlarni olishni davom ettirish uchun biz bilan bog‘laning{contact}.",
    },
    "pilot_over": {
        "ru": "Срок доступа вашего агентства к Makon Radar закончился. Чтобы объявления снова приходили, выберите тариф 👇",
        "uz": "Agentligingizning Makon Radar’dan foydalanish muddati tugadi. E’lonlar yana kelishi uchun tarifni tanlang 👇",
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
    "menu_tariff": {"ru": "💳 Тариф", "uz": "💳 Tarif"},
    "menu_shown": {"ru": "Меню внизу экрана 👇", "uz": "Menyu ekranning pastida 👇"},
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
    "dz_btn": {"ru": "⭐ Дильнозе", "uz": "⭐ Dilnozaga"},
    "dz_done_btn": {"ru": "✅ У Дильнозы", "uz": "✅ Dilnozada"},
    "dz_ok": {"ru": "Передано Дильнозе, теперь она знает этот объект",
              "uz": "Dilnozaga yuborildi, endi u bu obyektni biladi"},
    "dz_fail": {"ru": "Не получилось передать, попробуйте позже",
                "uz": "Yuborib bo‘lmadi, keyinroq urinib ko‘ring"},
    "export_caption": {
        "ru": "Объявления за 7 дней по вашим фильтрам",
        "uz": "Filtrlaringiz bo‘yicha 7 kunlik e’lonlar",
    },
    # --- тарифы и оплата ---
    "level_lite": {"ru": "Лайт", "uz": "Layt"},
    "level_standard": {"ru": "Стандарт", "uz": "Standart"},
    "level_pro": {"ru": "Pro", "uz": "Pro"},
    "level_trial": {"ru": "пробный период", "uz": "sinov muddati"},
    "tariff_title": {
        "ru": "<b>Тарифы Makon Radar</b>, оплата за {days} дней:\n\n"
              "🔹 <b>Лайт — {lite} сум</b>\n{lite_seats}. До 3 районов, подборка новых объявлений раз в час.\n\n"
              "🔸 <b>Стандарт — {standard} сум</b>\n{standard_seats}. Все районы, новые объявления сразу, проверка каждые 10 минут.\n\n"
              "⭐ <b>Pro — {pro} сум</b>\n{pro_seats}. Всё из Стандарта, плюс пометка «ниже рынка» и без повторных объявлений одного объекта.\n\n"
              "Цена за всё агентство. Дополнительный сотрудник сверх тарифа — по договорённости.\n\n"
              "{current}Выберите тариф:",
        "uz": "<b>Makon Radar tariflari</b>, {days} kunlik to‘lov:\n\n"
              "🔹 <b>Layt — {lite} so‘m</b>\n{lite_seats}. 3 tagacha tuman, yangi e’lonlar to‘plami soatiga bir marta.\n\n"
              "🔸 <b>Standart — {standard} so‘m</b>\n{standard_seats}. Barcha tumanlar, yangi e’lonlar darhol, har 10 daqiqada tekshiruv.\n\n"
              "⭐ <b>Pro — {pro} so‘m</b>\n{pro_seats}. Standartdagi hammasi, bundan tashqari «bozordan arzon» belgisi va bitta obyektning takroriy e’lonlarisiz.\n\n"
              "Narx butun agentlik uchun. Tarifdan tashqari qo‘shimcha xodim — kelishuv asosida.\n\n"
              "{current}Tarifni tanlang:",
    },
    "tariff_current": {"ru": "Сейчас у вас: {level}, до {date}.\n\n", "uz": "Hozir sizda: {level}, {date} gacha.\n\n"},
    "tariff_btn": {"ru": "{level} — {amount} сум", "uz": "{level} — {amount} so‘m"},
    "choose_tariff_btn": {"ru": "💳 Выбрать тариф", "uz": "💳 Tarifni tanlash"},
    "extend_btn": {"ru": "💳 Продлить", "uz": "💳 Uzaytirish"},
    "pay_info": {
        "ru": "Тариф <b>{level}</b>: {amount} сум за {days} дней.\n\n"
              "Переведите <b>{amount} сум</b> на карту HUMO:\n<code>{card}</code>{owner}\n\n"
              "После перевода нажмите «Я оплатил». Мы проверим поступление и включим тариф, обычно в течение часа.",
        "uz": "<b>{level}</b> tarifi: {days} kun uchun {amount} so‘m.\n\n"
              "<b>{amount} so‘m</b>ni HUMO kartasiga o‘tkazing:\n<code>{card}</code>{owner}\n\n"
              "O‘tkazgandan so‘ng «To‘ladim» tugmasini bosing. Tushumni tekshirib, tarifni yoqamiz, odatda bir soat ichida.",
    },
    "paid_btn": {"ru": "✅ Я оплатил", "uz": "✅ To‘ladim"},
    "click_btn": {"ru": "💙 Оплатить через Click", "uz": "💙 Click orqali to‘lash"},
    "click_info": {
        "ru": "\n\nИли через Click: нажмите кнопку «Оплатить через Click» и введите сумму <b>{amount} сум</b>, потом тоже нажмите «Я оплатил».",
        "uz": "\n\nYoki Click orqali: «Click orqali to‘lash» tugmasini bosing va <b>{amount} so‘m</b> summasini kiriting, so‘ng «To‘ladim» tugmasini bosing.",
    },
    "click_ussd": {
        "ru": "\nБез интернета: наберите <code>{ussd}</code>",
        "uz": "\nInternetsiz: <code>{ussd}</code> ni tering",
    },
    "other_tariff_btn": {"ru": "⬅️ Другой тариф", "uz": "⬅️ Boshqa tarif"},
    "pay_sent": {
        "ru": "Спасибо! Проверяем оплату. Как только подтвердим, я напишу и включу тариф.",
        "uz": "Rahmat! To‘lovni tekshiryapmiz. Tasdiqlashimiz bilan yozaman va tarifni yoqaman.",
    },
    "pay_confirmed": {
        "ru": "Оплата подтверждена ✅ Тариф {level} включён до {date} включительно.",
        "uz": "To‘lov tasdiqlandi ✅ {level} tarifi {date} gacha (shu kun ham kiradi) yoqildi.",
    },
    "pay_confirmed_lite": {
        "ru": "\n\nНа тарифе Лайт выберите от 1 до 3 районов: «⚙️ Фильтры» → «Районы». Подборка будет приходить раз в час.",
        "uz": "\n\nLayt tarifida 1 tadan 3 tagacha tuman tanlang: «⚙️ Filtrlar» → «Tumanlar». To‘plam soatiga bir marta keladi.",
    },
    "pay_rejected": {
        "ru": "Мы не нашли ваш перевод. Если вы уже оплатили, напишите нам{contact}.",
        "uz": "O‘tkazmangizni topmadik. Agar to‘lagan bo‘lsangiz, bizga yozing{contact}.",
    },
    "lite_max": {
        "ru": "На тарифе Лайт можно выбрать до 3 районов. Больше районов — на тарифе Стандарт («💳 Тариф»).",
        "uz": "Layt tarifida 3 tagacha tuman tanlash mumkin. Ko‘proq tuman — Standart tarifida («💳 Tarif»).",
    },
    "lite_need_district": {
        "ru": "На тарифе Лайт выберите от 1 до 3 районов, иначе подборка не придёт.",
        "uz": "Layt tarifida 1 tadan 3 tagacha tuman tanlang, aks holda to‘plam kelmaydi.",
    },
    "digest_head": {"ru": "🕐 Новые объявления за час: {n}", "uz": "🕐 So‘nggi bir soatdagi yangi e’lonlar: {n}"},
    "digest_more": {
        "ru": "…и ещё {n}. Все объявления есть в «📊 Выгрузка в Excel».",
        "uz": "…yana {n} ta. Barcha e’lonlar «📊 Excelga yuklash» bo‘limida.",
    },
    "below_market": {
        "ru": "🔥 Ниже рынка на {pct}% (по цене за м² в этом районе)",
        "uz": "🔥 Bozordan {pct}% arzon (shu tumandagi 1 m² narxi bo‘yicha)",
    },
    "feedback_ask": {
        "ru": "Здравствуйте! Это Раиль, Makon Radar. Ваш пробный период скоро заканчивается. "
              "Подскажите, пожалуйста, как вам бот: попадались полезные объявления от собственников, "
              "чего не хватает? Просто ответьте на это сообщение, пара слов очень поможет его улучшить. "
              "Если хотите продолжить, расскажу об условиях.\n\n"
              "И ещё: посмотрите нашего ИИ-ассистента Дильнозу @makon_dilnoza_bot. Она сама отвечает "
              "клиентам агентства в Telegram, подбирает квартиры с фото и записывает на просмотр, "
              "а объекты из Radar добавляются к ней кнопкой «⭐ Дильнозе».",
        "uz": "Assalomu alaykum! Bu Rail, Makon Radar. Sinov muddatingiz yaqinda tugaydi. "
              "Bot sizga qanday bo‘ldi: egasidan foydali e’lonlar chiqdimi, nima yetishmayapti? "
              "Shu xabarga javob yozing, bir-ikki so‘z botni yaxshilashga juda yordam beradi. "
              "Davom ettirmoqchi bo‘lsangiz, shartlarini aytib beraman.\n\n"
              "Yana bir narsa: AI-yordamchimiz Dilnozani ko‘rib chiqing @makon_dilnoza_bot. U agentlik "
              "mijozlariga Telegramda o‘zi javob beradi, rasm bilan kvartira tanlaydi va ko‘rishga yozib "
              "qo‘yadi, Radar’dagi obyektlar unga «⭐ Дильнозе» tugmasi bilan qo‘shiladi.",
    },
    "access_soon": {
        "ru": "{date} заканчивается ваш доступ к Makon Radar. Чтобы объявления приходили без перерыва, продлите тариф 👇",
        "uz": "{date} kuni Makon Radar’dan foydalanish muddati tugaydi. E’lonlar uzilishsiz kelishi uchun tarifni uzaytiring 👇",
    },
}


def t(key: str, lang: str) -> str:
    return T[key].get(lang) or T[key]["ru"]


def district_name(key: str, lang: str) -> str:
    ru, uz, _ = DISTRICTS[key]
    return uz if lang == "uz" else ru


# Команды для кнопки «Меню» слева от поля ввода
COMMANDS = {
    "ru": [("menu", "Показать меню"), ("filters", "Фильтры"), ("latest", "Последние объявления"),
           ("export", "Выгрузка в Excel"), ("pause", "Пауза / включить рассылку"), ("team", "Моя команда"),
           ("lang", "Язык"), ("tariff", "Тариф и оплата"), ("start", "Начать заново")],
    "uz": [("menu", "Menyuni ko‘rsatish"), ("filters", "Filtrlar"), ("latest", "So‘nggi e’lonlar"),
           ("export", "Excelga yuklash"), ("pause", "To‘xtatish / yoqish"), ("team", "Jamoam"), ("lang", "Til"),
           ("tariff", "Tarif va to‘lov"), ("start", "Qaytadan boshlash")],
}
