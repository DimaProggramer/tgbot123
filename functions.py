import requests
from decimal import Decimal
from aiocryptopay import AioCryptoPay, Networks
import json
import asyncio

CRYPTO_TOKEN = ""
crypto_client = AioCryptoPay(CRYPTO_TOKEN, network=Networks.TEST_NET)

def get_conversion_rate(fsym, tsym='RUB'):
    url = f'https://min-api.cryptocompare.com/data/price?fsym={fsym}&tsyms={tsym}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data.get(tsym, 99999999)
    else:
        raise Exception("Ошибка при получении курса валют: " + response.text)


with open("soft_data.json", "r") as f:
    SOFT_DATA = json.load(f)

def get_rates(fsym, tsym_list):
    tsym = ','.join(tsym_list)
    url = f'https://min-api.cryptocompare.com/data/price?fsym={fsym}&tsyms={tsym}'
    return requests.get(url).json()

def rub_to_ton(amount):
    rates = get_rates("RUB", ["TON"])
    rate = Decimal(rates.get("TON", 0))
    if rate == 0:
        raise ValueError("Курс TON не найден")
    return amount * rate

def ton_to_other(ton_amount, tsym):
    rates = get_rates("TON", [tsym])
    rate = Decimal(rates.get(tsym, 0))
    if rate == 0:
        raise ValueError(f"Курс {tsym} не найден")
    return ton_amount * rate

async def send_to_channel(user_id):
    data = user_data[user_id]
    text = data["text"]
    photo = data["photo"]
    link = data["link"]

    keyboard = types.InlineKeyboardMarkup().add(types.inlineKeyboardButton("Подробнее...", url=link))

    if photo:
        await bot.send_photo(chat_id=CHANNEL_ID[0], photo=photo, caption=text, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=CHANNEL_ID[0], text=text, reply_markup=keyboard)

    del user_data[user_id]

async def send_file_info(user_id, file_name):
    file_info = SOFT_DATA["soft"][file_name]
    response_message = (
        f"Ссылка: {file_info['link']}\n"
        f"Название: {file_info['name']}\n"
        f"Описание: {file_info['description']}\n"
        f"Цена: {file_info['price_rub']} рублей"
    )
    return response_message
