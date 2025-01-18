from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiocryptopay import AioCryptoPay, Networks
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
import requests
from decimal import Decimal
import sqlite3
from functions import *
from database_functions import *
API_TOKEN = ""
ADMIN_IDS = ("", "")
CHANNEL_ID = 
CHANNEL_LINK = ""
IMAGES_DIR = "broadcast_images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS broadcasts (id INTEGER PRIMARY KEY, text TEXT)''')
conn.commit()

class Form(StatesGroup):
    waiting_for_content = State()
    waiting_for_news_number = State()
    change_news_settings = State()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            insert_user(user_id)

            kb = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("👤 Личный кабинет", callback_data="user_panel"),
                types.InlineKeyboardButton("💲 Прайс", callback_data="show_price"),
                types.InlineKeyboardButton("🛒 Купить", callback_data="buy_soft"),
                types.InlineKeyboardButton("👩‍💻 Т/П", callback_data="tech"),
                types.InlineKeyboardButton("📰 Последние новости", callback_data="last_news")
            )
            await message.answer("👋 Добро пожаловать в бота!", reply_markup=kb)
        else:
            await message.answer(
                "🚫 Подпишитесь на каналы для использования бота:\n"
                f"[Подписаться на канал]({CHANNEL_LINK})\n",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_subscription")
                ),
                parse_mode='Markdown'
            )
    except Exception as e:
        await message.answer("❌ Произошла ошибка при проверке подписки. Попробуйте позже.")
        print(e)


@dp.callback_query_handler(text="check_subscription")
async def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            insert_user(user_id)

            await call.message.edit_text("✅ Вы успешно подписаны на канал! Теперь вы можете использовать бота.")
            kb = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("👤 Личный кабинет", callback_data="user_panel"),
                types.InlineKeyboardButton("💲 Прайс", callback_data="show_price"),
                types.InlineKeyboardButton("🛒 Купить", callback_data="buy_soft"),
                types.InlineKeyboardButton("👩‍💻 Т/П", callback_data="tech"),
                types.InlineKeyboardButton("📰 Последние новости", callback_data="last_news")
            )
            await call.message.answer("Добро пожаловать!", reply_markup=kb)
        else:
            await call.answer("🚫 Вы не подписаны на канал.", show_alert=True)
    except Exception as e:
        await call.answer("❌ Произошла ошибка при проверке подписки.", show_alert=True)
        print(e)


@dp.callback_query_handler(lambda call: call.data == "user_panel")
async def user_panel(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.answer(
        f"💰 Личный кабинет\n\n👤 ID: {user_id}",
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu")
        )
    )


@dp.callback_query_handler(lambda call: call.data == "tech")
async def tech_support(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.answer(
        f"Текст Т/П",
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu")
        )
    )


@dp.message_handler(commands=["admin_panel"])
async def admin_panel(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) not in ADMIN_IDS:
        await message.answer("❌ У вас недостаточно прав для доступа к админ панели.")
        return
    
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("📣 Рассылка", callback_data="send_broadcast"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="show_statistics"),
        types.InlineKeyboardButton("🆕Переучет новостей", callback_data="inventory"),
        types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu"),
    )
    await message.reply(f"🛠 Админ панель", reply_markup=kb)


@dp.callback_query_handler(lambda call: call.data == "inventory")
async def recount_news(call: types.CallbackQuery):
    news = get_last_news_from_db()
    if news:
        news_texts = []
        callback_data = None

        for idx, item in enumerate(news, start=1):
            news_texts.append(f"{idx}. {item[1]}")
            if not callback_data:
                callback_data = f'delete_news_{item[0]}'

        final_news_text = "\n".join(news_texts)

        inline_kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🚮 Удалить новость", callback_data=callback_data)
        )

        await call.message.answer(final_news_text, reply_markup=inline_kb)
    else:
        await call.message.answer("или это ошибка базы, или тут реально ничего нету")
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == "show_price")
async def show_price(call: types.CallbackQuery):
    text = "💲 Прайс на софт:\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for file, details in SOFT_DATA["soft"].items():
        text += f"🔹 {details['name']} — {details['price_rub']} RUB\n📄 Описание: {details['description']}\n"
    user_id = call.message.from_user.id
    kb.add(types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu"))
    await call.message.reply(text, reply_markup=kb)


@dp.callback_query_handler(lambda call: call.data.startswith("buy_soft"))
async def process_payment(call: types.CallbackQuery):
    user_id = call.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for file, details in SOFT_DATA["soft"].items():
        kb.add(types.InlineKeyboardButton(f"🛒 {details['name']}", callback_data=f"pay:{file}"))
    
    kb.add(types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu"))
    await call.message.reply("Выберите софт для покупки:", reply_markup=kb)


@dp.callback_query_handler(lambda call: call.data.startswith("pay"))
async def handle_payment(call: types.CallbackQuery):
    file_name = call.data.split(":")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)

    for asset in ["TON", "BTC", "ETH", "USDT"]: 
        kb.add(types.InlineKeyboardButton(f"💰 Оплатить через {asset}", callback_data=f"confirm_pay:{file_name}:{asset}"))
    
    kb.add(types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu"))
    await call.message.reply("Выберите криптовалюту для оплаты:", reply_markup=kb)

@dp.callback_query_handler(lambda call: call.data.startswith("confirm_pay"))
async def confirm_payment(call: types.CallbackQuery):
    await call.message.delete()
    _, file_name, asset = call.data.split(":")
    user_id = call.from_user.id
    price_rub = Decimal(SOFT_DATA["soft"][file_name]["price_rub"])

    crypto_rate = get_conversion_rate(asset.upper())
    if crypto_rate:
        crypto_rate_decimal = Decimal(crypto_rate)
        price_crypto = price_rub / crypto_rate_decimal
    else:
        price_crypto = Decimal(99999999999)

    price_crypto_float = float(price_crypto)

    invoice = await crypto_client.create_invoice(
        asset=asset,
        amount=price_crypto_float,
        description=f"Покупка {SOFT_DATA['soft'][file_name]['name']}"
    )
    payment_link = invoice.pay_url
    await call.message.answer(f"💵 Ссылка для оплаты через {asset}:\n{payment_link}")
    await asyncio.create_task(check_payment(invoice.invoice_id, file_name, user_id, call.message))

async def check_payment(invoice_id, file_name, user_id, message):
    for _ in range(36):
        global crypto_client
        invoices = await crypto_client.get_invoices(invoice_ids=[invoice_id])
        if invoices and invoices[0].status == 'paid':
            response_message = await send_file_info(user_id, file_name)
            await bot.send_message(user_id, response_message)
            return
        await asyncio.sleep(5)
    await bot.send_message(user_id, "⏰ Время оплаты истекло. Платёж не был завершён.")

@dp.callback_query_handler(lambda call: call.data == "return_to_menu")
async def return_to_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("👤 Личный кабинет", callback_data="user_panel"),
        types.InlineKeyboardButton("💲 Прайс", callback_data="show_price"),
        types.InlineKeyboardButton("🛒 Купить", callback_data="buy_soft"),
        types.InlineKeyboardButton("👩‍💻 Т/П", callback_data="tech"),
        types.InlineKeyboardButton("📰 Последние новости", callback_data="last_news")
    )
    await call.message.answer("Главное меню", reply_markup=kb)

@dp.message_handler(commands=["post"])
async def start_command(message: types.Message):
    if str(message.from_user.id) in ADMIN_IDS:
        await message.reply("Пришлите фото:")
        user_data[message.from_user.id] = {"photo": None, "text": None, "link": None}
    else:
        await message.reply("У вас нет доступа.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    if message.from_user.id in user_data and user_data[message.from_user.id]["photo"] is None:
        user_data[message.from_user.id]["photo"] = message.photo[-1].file_id
        await message.reply("Пришлите текст рекламы:")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    if message.from_user.id in user_data:
        if user_data[message.from_user.id]["photo"] is None:
            await message.reply("Пришлите текст рекламы:")
        elif user_data[message.from_user.id]["text"] is None:
            user_data[message.from_user.id]["text"] = message.text
            await message.reply("Пришлите ссылку для кнопки:")
        elif user_data[message.from_user.id]["link"] is None:
            user_data[message.from_user.id]

@dp.callback_query_handler(lambda call: call.data == "send_broadcast")
async def send_broadcast(call: types.CallbackQuery):
    user_id = call.from_user.id
    if str(user_id) not in ADMIN_IDS:
        await call.answer("❌ У вас недостаточно прав для доступа к этой функции.")
        return

    await call.message.answer("Введите сообщение для рассылки:")
    await Form.waiting_for_content.set()


@dp.message_handler(state=Form.waiting_for_content, content_types=['text', 'photo'])
async def process_broadcast(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) not in ADMIN_IDS:
        await message.answer("❌ У вас недостаточно прав для доступа к этой функции.")
        return

    content = message.text or message.caption
    cursor.execute("INSERT INTO broadcasts (text) VALUES (?)", (content,))
    conn.commit()

    photo_path = None
    if message.photo:
        photo = message.photo[-1]
        photo_path = os.path.join(IMAGES_DIR, f"broadcast_{photo.file_id}.jpg")
        await photo.download(photo_path)
    user_ids = cursor.execute("SELECT user_id FROM users").fetchall()
    for (user_id,) in user_ids:
        try:
            if photo_path:
                await bot.send_photo(user_id, photo=open(photo_path, 'rb'), caption=content)
            else:
                await bot.send_message(user_id, text=content)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    await message.answer("✅ Рассылка завершена.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('delete_news_'))
async def confirm_delete_news(callback_query: types.CallbackQuery):
    news_id = callback_query.data.split('_')[-1]
    await bot.answer_callback_query(callback_query.id)

    await Form.waiting_for_news_number.set()
    async with dp.current_state(user=callback_query.from_user.id).proxy() as data:
        data['news_id'] = news_id

    await bot.send_message(callback_query.from_user.id, f"Введите номер новости для удаления (отмена чтобы выйти):")

@dp.message_handler(state=Form.waiting_for_news_number)
async def delete_news(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        news_id = data['news_id']

    if message.text.lower() == 'отмена':
        await state.finish()
        await message.answer("🔙Удаление отменено")
    else:
        try:
            news_id = int(news_id)
            cursor.execute("DELETE FROM broadcasts WHERE id=?", (news_id,))
            conn.commit()
            await state.finish()
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("🏠 Вернуться в меню", callback_data="return_to_menu"))
            await message.answer("🚮Новость удалена.", reply_markup=kb)
        except ValueError:
            await message.answer("❌Введите корректный номер новости.")

@dp.callback_query_handler(lambda call: call.data == "show_statistics")
async def show_statistics(call: types.CallbackQuery):
    user_id = call.from_user.id
    if str(user_id) not in ADMIN_IDS:
        await call.answer("❌ У вас недостаточно прав для доступа к этой функции.")
        return
    
    
    total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await call.message.answer(f"📊 Статистика:\n👥 Всего пользователей: {total_users}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    