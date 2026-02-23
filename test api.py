import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

logging.basicConfig(level=logging.INFO)

bot = Bot(token="token_bot")
dp = Dispatcher()

def get_kemerovo_air_owm():
    api_key = "API_openweathe"
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

            res = (
                f"--- Экология Кемерово ---\n"
                f"📊 Оценка качества(5-1): {aqi}\n"
                f"📊 Индекс качества: {status}\n"
                f"🌫 Частицы PM2.5: {pm2_5} мкг/м³\n"
                f"💨 Угарный газ (CO): {co} мкг/м³\n"
            )

            if aqi >= 4:
                res += "\n⚠️ СОВЕТ: На улице смог, закройте окна!"
            else:
                res += "\n✅ СОВЕТ: Воздух в норме."

            return res
        else:
            return "❌ Ошибка сервера OpenWeather."
    except Exception as e:
        return f"💥 Ошибка соединения: {e}"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text='AQI(Кем)')]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Выберите действие'
    )
    await message.answer('Привет! Нажмите на кнопку ниже, чтобы узнать качество воздуха.', reply_markup=keyboard)


@dp.message(F.text == 'AQI(Кем)')
async def aqi_handler(message: types.Message):
    report = get_kemerovo_air_owm()
    await message.answer(report)


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
