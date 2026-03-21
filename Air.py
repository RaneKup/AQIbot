import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


logging.basicConfig(level=logging.INFO)
bot = Bot(token="8248324489:AAEsb5wWvewYTTUc-nH2r1dJ-sVoz2HAhMw")
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text='AQI(Кем)')]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Приветствуем в AirBot'
    )
    await message.answer('Качество воздуха в Кемерове', reply_markup=keyboard)

@dp.message(Command("AQI(Кем)"))
async def AQI(message: types.Message):
    def get_kemerovo_air_owm(api_key):
        lat = 55.33
        lon = 86.08

        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                aqi = data['list'][0]['main']['aqi']

                components = data['list'][0]['components']
                pm2_5 = components['pm2_5']
                co = components['co']

                interpret = {
                    1: "🟢 Отлично (Чистый воздух)",
                    2: "🟡 Сойдет (Умеренно)",
                    3: "🟠 Средне (Вредно для чувствительных людей)",
                    4: "🔴 Плохо (Загрязненный воздух)",
                    5: "💀 Очень плохо (Опасный смог)"
                }

                status = interpret.get(aqi, "Неизвестно")

                print(f"--- Экология Кемерово (OpenWeather) ---")
                print(f"📊 Индекс качества (1-5): {aqi}")
                print(f"📢 Статус: {status}")
                print(f"---------------------------------------")
                print(f"🌫 Частицы PM2.5: {pm2_5} мкг/м³")
                print(f"💨 Угарный газ (CO): {co} мкг/м³")

                if aqi >= 4:
                    print("⚠️ СОВЕТ: На улице сильный смог, закройте окна и включите очиститель воздуха.")
                else:
                    print("✅ СОВЕТ: Уровень загрязнения в норме.")

            else:
                print(f"❌ Ошибка сервера: {data.get('message', 'Нет описания')}")

        except Exception as e:
            print(f"💥 Ошибка соединения: {e}")

    MY_OWM_KEY = "ce05754746ed917ae04cf1d9604abd56"
    get_kemerovo_air_owm(MY_OWM_KEY)
    await message.answer(f'{get_kemerovo_air_owm(MY_OWM_KEY)}')


async def main():
    await dp.start_polling(bot)

asyncio.run(main())