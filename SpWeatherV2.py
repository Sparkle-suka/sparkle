# meta developer: @Nik4mnost <2347>
# meta banner: https://x0.at/FJ51.png
import aiohttp
from .. import loader, utils


@loader.tds
class SpWeatherMod(loader.Module):
    """Модуль погоды SpWeather"""

    strings = {"name": "SpWeather"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "default_city",
                "Москва",
                lambda: "Город по умолчанию",
            )
        )

    async def client_ready(self, client, db):
        self.api_key = "1f4635ac7fdae9c54944622cfda14ca6"

    def get_weather_emoji(self, main_status, description):
        """Эмодзи статус погоды"""
        main_status = main_status.lower()
        desc = description.lower()

        if "thunderstorm" in main_status:
            return "<tg-emoji emoji-id=5282731554135615450>🌩</tg-emoji>"
        elif "drizzle" in main_status:
            return "💦"
        elif "rain" in main_status:
            if "ливень" in desc or "сильный" in desc:
                return "<tg-emoji emoji-id=5282731554135615450>🌩</tg-emoji>"
            return "🌧"
        elif "snow" in main_status:
            return "<tg-emoji emoji-id=5282833267551117457>🌨</tg-emoji>"
        elif "clear" in main_status:
            return "<tg-emoji emoji-id=5469947168523558652>☀️</tg-emoji>"
        elif "clouds" in main_status:
            if "малооблачно" in desc or "небольшая облачность" in desc:
                return "<tg-emoji emoji-id=5350424168615649565>⛅️</tg-emoji>"
            elif "переменная" in desc:
                return "<tg-emoji emoji-id=5350424168615649565>⛅️</tg-emoji>"
            return "<tg-emoji emoji-id=5287571024500498635>☁️</tg-emoji>"
        elif main_status in ["mist", "smoke", "haze", "dust", "fog", "sand", "ash", "squall", "tornado"]:
            return "🌫️"
        
        return "📝"

    def _build_current_text(self, location, data):
        """Я урод"""
        temp = int(round(data.get("main", {}).get("temp", 0)))
        feels_like = int(round(data.get("main", {}).get("feels_like", 0)))
        humidity = data.get("main", {}).get("humidity", 0)
        wind_speed = data.get("wind", {}).get("speed", 0)
        
        weather_obj = data.get("weather", [{}])[0]
        main_status = weather_obj.get("main", "")
        description = weather_obj.get("description", "").capitalize()
        
        status_emoji = self.get_weather_emoji(main_status, description)

        return (
            f"<b>🌦 Погода: {location}</b>\n\n"
            f"<b>📊 Текущая погода:</b>\n"
            f"<b>🌡️ Температура: {temp}°C</b>\n"
            f"<b>-- Ощущается как: {feels_like}°C</b>\n"
            f"<b>💧 Влажность: {humidity}%</b>\n"
            f"<b>💨 Ветер: {wind_speed} м/с</b>\n"
            f"<b>{status_emoji} Описание: {description}</b>"
        )

    @loader.command()
    async def weather(self, message):
        """[город](либо указать в кфг) - Получить текущую погоду"""
        args = utils.get_args_raw(message)

        if not args:
            query = self.config["default_city"].strip()
        else:
            query = args.strip()

        if not query:
            await message.edit("<b>❌ Город не указан ни в команде, ни в конфиге!</b>")
            return

        await message.edit(f"<b>🔍 Ищу локацию <code>{query}</code>...</b>")

        clean_query = query.replace(",", " ").replace(".", " ")
        words = [w for w in clean_query.split() if w]

        if not words:
            await message.edit("<b>❌ Некорректный ввод города.</b>")
            return

        search_name = words[0]

        geo_url = "https://api.openweathermap.org/geo/1.0/direct"
        geo_params = {"q": search_name, "limit": 5, "appid": self.api_key}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(geo_url, params=geo_params) as geo_response:
                    if geo_response.status != 200:
                        await message.edit(f"<b>❌ Ошибка геокодинга API (Код: {geo_response.status})</b>")
                        return

                    geo_data = await geo_response.json()
                    if not geo_data:
                        await message.edit(f"<b>❌ Город <code>{search_name}</code> не найден в базе.</b>")
                        return

                    target_location = geo_data[0]
                    if len(words) > 1:
                        additional_inputs = [w.lower() for w in words[1:]]
                        for res in geo_data:
                            state = str(res.get("state", "")).lower()
                            country = str(res.get("country", "")).lower()
                            if any(inp in state or inp in country for inp in additional_inputs):
                                target_location = res
                                break
                            if "кбр" in additional_inputs and ("kabardin" in state or "кабардин" in state):
                                target_location = res
                                break

                    lat = target_location.get("lat")
                    lon = target_location.get("lon")
                    
                    local_names = target_location.get("local_names", {})
                    city_name = local_names.get("ru", target_location.get("name"))
                    state_name = target_location.get("state", "")
                    
                    full_location_name = f"{city_name}, {state_name}" if state_name else f"{city_name}"

                # Получение текущей погоды
                weather_url = "https://api.openweathermap.org/data/2.5/weather"
                weather_params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "lang": "ru"}

                async with session.get(weather_url, params=weather_params) as weather_response:
                    if weather_response.status == 200:
                        data = await weather_response.json()
                        text = self._build_current_text(full_location_name, data)

                        reply_markup = [
                            [
                                {"text": "🗓️ 3 дня","style":"primary", "callback": self._inline_forecast, "args": (lat, lon, 3, text)},
                                {"text": "🗓️ 7 дней","style":"primary","callback": self._inline_forecast, "args": (lat, lon, 7, text)}
                            ],
                            [
                                {"text": "🗑️ Скрыть прогноз","style":"danger","callback": self._inline_close, "args": (text,)}
                            ]
                        ]

                        await self.inline.form(text=text, message=message, reply_markup=reply_markup)
                    else:
                        await message.edit(f"<b>❌ Ошибка OpenWeatherMap API (Код: {weather_response.status})</b>")

            except Exception as e:
                await message.edit(f"<b>❌ Ошибка:</b> <code>{str(e)}</code>")

    async def _inline_forecast(self, call, lat, lon, days, base_text):
        """Инлайн-метод получения прогноза на 3/7 дней в новом дизайне"""
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "lang": "ru"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(forecast_url, params=forecast_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecast_list = data.get("list", [])

                        forecast_text = f"{base_text}\n\n<b>🗓️ Прогноз на {days} дн.:</b>\n"
                        
                        shown_days = 0
                        last_date = ""
                        
                        for item in forecast_list:
                            dt_txt = item.get("txt_str", item.get("dt_txt", ""))
                            if not dt_txt:
                                continue
                            
                            date_part, time_part = dt_txt.split(" ")
                            if date_part == last_date:
                                continue
                            
                            if "12:00" in time_part or shown_days == 0:
                                last_date = date_part
                                # Преобразуем YYYY-MM-DD в ДД.ММ
                                _, mm, dd = date_part.split("-")
                                date_formatted = f"{dd}.{mm}"
                                
                                temp_min = int(round(item.get("main", {}).get("temp_min", 0)))
                                temp_max = int(round(item.get("main", {}).get("temp_max", 0)))
                                
                                weather_obj = item.get("weather", [{}])[0]
                                main_status = weather_obj.get("main", "")
                                desc = weather_obj.get("description", "").lower()
                                
                                day_emoji = self.get_weather_emoji(main_status, desc)
                                
                                # Добавил переменную desc в конец строки, чтобы писался текст погоды
                                forecast_text += f"▫️ {date_formatted} {day_emoji} {temp_min}...{temp_max}°C, {desc}\n"
                                shown_days += 1
                                
                                if shown_days >= days:
                                    break

                        reply_markup = [
                            [
                                {"text": "🗓️ 3 дня","style":"primary", "callback": self._inline_forecast, "args": (lat, lon, 3, base_text)},
                                {"text": "🗓️ 7 дней","style":"primary","callback": self._inline_forecast, "args": (lat, lon, 7, base_text)}
                            ],
                            [
                                {"text": "🗑️ Скрыть прогноз","style":"danger", "callback": self._inline_close, "args": (base_text,)}
                            ]
                        ]
                        await call.edit(text=forecast_text, reply_markup=reply_markup)
                    else:
                        await call.answer("Ошибка получения прогноза OWM.")
            except Exception:
                await call.answer("Ошибка соединения с OpenWeatherMap.")

    async def _inline_close(self, call, base_text):
        # Метод delete() полностью удаляет это сообщение
        await call.delete()
