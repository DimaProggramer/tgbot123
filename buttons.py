from aiogram import types

def get_main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("👤 Личный кабинет", callback_data="user_panel"),
        types.InlineKeyboardButton("💲 Прайс", callback_data="show_price"),
        types.InlineKeyboardButton("🛒 Купить", callback_data="buy_soft"),
        types.InlineKeyboardButton("👩‍💻 Т/П", callback_data="tech"),
        types.InlineKeyboardButton("📰 Последние новости", callback_data="last_news")
    )
    return kb
    