# meta developer: @Nik4mnost
# scope: hikka_only

import logging
import aiohttp
from datetime import datetime
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class GismeteoWeatherMod(loader.Module):
    #Погодный модуль для ру городов [Gismeteo]
    strings = {
        "name": "GismeteoWeather",
        "loading": "<b>⏳ Загрузка метеоданных...</b>",
        "header": "<b>🌦 Погода: {}</b>\n\n",
        "current_sect": (
            "<b>📊 Текущая погода:</b>\n"
            "🌡 Температура: <code>{}°C</code>\n"
            "-- <i>Ощущается как: {}°C</i>\n"
            "💧 Влажность: <code>{}%</code>\n"
            "💨 Ветер: <code>{} м/с</code>\n"
            "📝 Описание: <code>{}</code>\n\n"
        ),
        "error": "<b>❌ Ошибка:</b> <code>{}</code>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "default_city", "Прохладный", "Город по умолчанию "
        )

    async def weathercmd(self, message):
        """Показывает погоду ""
        args = utils.get_args_raw(message)
        city = args if args else self.config["default_city"]
        city_search = city.split(",")[0].strip()
        
        message = await utils.answer(message, self.strings("loading"))
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Поиск города
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_search}&count=1&language=ru"
                async with session.get(geo_url) as res:
                    geo_data = await res.json()
                
                if not geo_data or not geo_data.get("results"):
                    return await utils.answer(message, f"<b>❌ Город '{city_search}' не найден.</b>")
                
                loc = geo_data["results"][0]
                # Отрисовка
                await self.render_weather(message, loc['latitude'], loc['longitude'], loc['name'], days=0)
            except Exception as e:
                logger.exception("Geo search error")
                await utils.answer(message, self.strings("error").format(str(e)))

    async def render_weather(self, target, lat, lon, city_name, days=0):
        # Кнопочка удалить
        if days == -1:
            try:
                if hasattr(target, "delete"):
                    await target.delete()
                else:
                    await target.obj.delete()
                return
            except Exception:
                return

        async with aiohttp.ClientSession() as session:
            try:
                # Запрос погоды
                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                    f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
                    f"&daily=weather_code,temperature_2m_max,temperature_2m_min&wind_speed_unit=ms&timezone=auto"
                )
                
                async with session.get(weather_url) as res:
                    data = await res.json()

                current = data["current"]
                text = self.strings("header").format(city_name)
                text += self.strings("current_sect").format(
                    round(current["temperature_2m"]), 
                    round(current["apparent_temperature"]),
                    current["relative_humidity_2m"], 
                    current["wind_speed_10m"],
                    self._get_desc(current["weather_code"])
                )

                # Блок прогноза
                if days > 0:
                    text += f"<b>📅 Прогноз на {days} дн.:</b>\n"
                    available_days = len(data["daily"]["time"]) - 1
                    for i in range(1, min(days + 1, available_days + 1)):
                        date_str = datetime.strptime(data["daily"]["time"][i], "%Y-%m-%d").strftime("%d.%m")
                        t_max = round(data["daily"]["temperature_2m_max"][i])
                        t_min = round(data["daily"]["temperature_2m_min"][i])
                        ico = self._get_ico(data["daily"]["weather_code"][i])
                        text += f"▫️ <code>{date_str}</code> {ico} <code>{t_min}...{t_max}°C</code>\n"

                # Кнопки
                btns = [
                    [
                        {"text": "📅 3 Дня","style":"primary", "callback": self._cb_handler, "args": (lat, lon, city_name, 3)},
                        {"text": "📅 7 Дней","style":"primary", "callback": self._cb_handler, "args": (lat, lon, city_name, 7)}
                    ],
                    [{"text": "🗑 Удалить прогноз","style":"danger", "callback": self._cb_handler, "args": (lat, lon, city_name, -1)}]
                ]

                # ОТПРАВКА
                try:
                    if hasattr(target, "edit") and not hasattr(target, "client"):
                        await target.edit(text=text, buttons=btns)
                    else:
                        await self.inline.form(text=text, message=target, buttons=btns)
                except Exception:
                    # Резервный вариант, если buttons= не сработает
                    if hasattr(target, "edit") and not hasattr(target, "client"):
                        await target.edit(text=text, reply_markup=btns)
                    else:
                        await self.inline.form(text=text, message=target, reply_markup=btns)

            except Exception as e:
                logger.exception("Weather render error")
                await utils.answer(target, self.strings("error").format(str(e)))

    async def _cb_handler(self, call, lat, lon, city_name, days):
        #Обработчик нажатий на инлайн-кнопки
        await self.render_weather(call, lat, lon, city_name, days)

    def _get_desc(self, code):
        #Перевод кодов Open-Meteo в текст
        codes = {
            0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
            45: "Туман", 48: "Иней", 51: "Легкая морось", 53: "Морось", 55: "Плотная морось",
            61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь", 71: "Снег", 73: "Снегопад",
            75: "Сильный снегопад", 77: "Снежная крупа", 80: "Ливень", 81: "Сильный ливень",
            82: "Очень сильный ливень", 95: "Гроза", 96: "Гроза с градом", 99: "Сильная гроза"
        }
        return codes.get(code, "Смешанные условия")

    def _get_ico(self, code):
        #иконки
        if code == 0: return "<tg-emoji emoji-id=5402477260982731644>☀️</tg-emoji>"
        if code in [1, 2]: return "<tg-emoji emoji-id=5350424168615649565>⛅️</tg-emoji>"
        if code == 3: return "☁️"
        if code in [45, 48]: return "🌫"
        if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "<tg-emoji emoji-id=5283243028905994049>🌧</tg-emoji>"
        if code in [71, 73, 75, 77, 85, 86]: return "<tg-emoji emoji-id=5449449325434266744>❄️</tg-emoji>"
        if code >= 95: return "<tg-emoji emoji-id=5282939632416206153>⛈</tg-emoji>"
        return "☁️"
