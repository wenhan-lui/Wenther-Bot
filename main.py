import os
import requests
import asyncio
import argparse
from datetime import time, datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

# Load .env secrets
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CITY = os.getenv("CITY", "Singapore")
USER_ID = int(os.getenv("USER_ID"))
UNITS = "metric"

# --- Weather Now ---
def get_current_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units={UNITS}"
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
    parser = argparse.ArgumentParser(description="Send weather update to Telegram")
    parser.add_argument("period", choices=["morning", "afternoon", "evening"], help="Which period to send update for")
    args = parser.parse_args()

    bot = Bot(BOT_TOKEN)
    print(f"✅ Sending weather update for: {args.period}")
    await send_weather_update(bot, args.period)

# --- Run it ---
if __name__ == "__main__":
    asyncio.run(main())
