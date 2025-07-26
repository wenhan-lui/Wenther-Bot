import os
import requests
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# --- Load .env config (if available) ---
BOT_TOKEN = '8146229564:AAFgu-CqqIzf9GPP5EEecKLcucWqxfiyaEY'
USER_ID = '354145612'
WEATHER_API_KEY = 'dfaf78baeca783e92343e9dae3b773a2'
CITY = 'Singapore'
UNITS = 'metric'

def get_current_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "main" not in data:
        return "⚠️ Could not fetch current weather."

    weather = data["weather"][0]["description"].capitalize()
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    return (
        f"🌤 *Current Weather in {CITY}*\n"
        f"Condition: {weather}\n"
        f"Temperature: {temp}°C (Feels like {feels_like}°C)\n"
        f"Humidity: {humidity}%\n"
        f"Wind Speed: {wind_speed} m/s"
    )

# --- Forecast helper ---
def get_forecast_for_time(target_hour):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={WEATHER_API_KEY}&units={UNITS}"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "list" not in data:
        return "⚠️ Could not fetch forecast data."

    now = datetime.now()
    target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if target_time < now:
        target_time += timedelta(days=1)

    closest = min(data["list"], key=lambda x: abs(datetime.fromtimestamp(x["dt"]) - target_time))
    dt_txt = closest["dt_txt"]
    weather = closest["weather"][0]["description"]
    temp = closest["main"]["temp"]
    feels_like = closest["main"]["feels_like"]

    return (
        f"🌤 *Forecast for {CITY} at {dt_txt}*\n"
        f"Weather: {weather.capitalize()}\n"
        f"Temp: {temp}°C (Feels like {feels_like}°C)"
    )

# --- Async message sender ---
async def send_weather_update(bot: Bot, period: str):
    hour_map = {"morning": 8, "afternoon": 13, "evening": 18}
    greeting_map = {
        "morning": "Good morning! 🌅",
        "afternoon": "Good afternoon! ☀️",
        "evening": "Good evening! 🌙"
    }

    if period == "morning":
        current = get_current_weather()
        forecast_1 = get_forecast_for_time(hour_map["afternoon"])
        forecast_2 = get_forecast_for_time(hour_map["evening"])
        message = f"{greeting_map[period]}\n\n{current}\n\n{forecast_1}\n\n{forecast_2}"
    elif period == "afternoon":
        current = get_current_weather()
        forecast_1 = get_forecast_for_time(hour_map["evening"])
        message = f"{greeting_map[period]}\n\n{current}\n\n{forecast_1}"
    else:
        current = get_current_weather()
        message = f"{greeting_map[period]}\n\n{current}"

    await bot.send_message(chat_id=USER_ID, text=message, parse_mode=ParseMode.MARKDOWN)

# --- Main async startup ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot = Bot(BOT_TOKEN)

    scheduler = AsyncIOScheduler()

    scheduler.add_job(send_weather_update, "cron", hour=8, minute=0, args=[bot, "morning"])
    scheduler.add_job(send_weather_update, "cron", hour=13, minute=0, args=[bot, "afternoon"])
    scheduler.add_job(send_weather_update, "cron", hour=18, minute=0, args=[bot, "evening"])

    scheduler.start()

    print("✅ Bot is running. You can test manually...")

    # Manual test on startup (optional)
    await send_weather_update(bot, "evening")

    # Keeps the app alive
    await app.run_polling()  # You can replace this with `idle()` if no handlers

# --- Run it ---
if __name__ == "__main__":
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError as e:
        print(f"Runtime error: {e}")
