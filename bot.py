import pytz
import os
import json
import random
import datetime
import requests
from telegram.ext import Updater
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Load content.json
with open("content.json", "r") as f:
    content = json.load(f)

# Load or create log.json
try:
    with open("log.json", "r") as f:
        log = json.load(f)
except FileNotFoundError:
    log = {
        "gm_used": [],
        "trading_used": [],
        "verses_used": [],
        "quotes_used": [],
        "prayers_used": [],
        "reminders_used": []
    }

# --- Utility: rotation with logging ---
def rotate_and_log(section, log_key):
    items = content.get(section, [])
    if not items:
        return {"message": "⚠️ No content available."}
    unused = [i for i in range(len(items)) if i not in log[log_key]]
    if not unused:
        log[log_key] = []
        unused = list(range(len(items)))
    choice = random.choice(unused)
    log[log_key].append(choice)
    with open("log.json", "w") as f:
        json.dump(log, f)
    return items[choice]

# --- Jobs ---
def good_morning_job(context):
    message = rotate_and_log("good_morning", "gm_used")["message"]
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def verse_of_the_day_job(context):
    try:
        ref = rotate_and_log("verses", "verses_used")
        response = requests.get(f"https://bible-api.com/{ref.replace(' ', '+')}", timeout=5)
        response.raise_for_status()
        data = response.json()
        verse_text = data["text"]
        message = f"✨ Verse of the Day:\n{verse_text.strip()}\n📖 {ref}"
    except Exception:
        verse = rotate_and_log("verses", "verses_used")
        message = f"✨ Verse of the Day (Fallback):\n{verse}"
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def daily_scripture_job(context):
    scripture = rotate_and_log("daily_scriptures", "verses_used")
    context.bot.send_message(chat_id=CHAT_ID, text=f"📖 Daily Scripture:\n{scripture}")

def trading_job(context):
    idea = rotate_and_log("trading", "trading_used")
    message = f"💹 Trading Idea:\n{idea['idea']}\n\n📖 {idea['scripture']}"
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def quote_job(context):
    quote = rotate_and_log("quotes", "quotes_used")
    context.bot.send_message(chat_id=CHAT_ID, text=f"🌟 Motivation:\n{quote}")

def prayer_job(context):
    prayer = rotate_and_log("prayers", "prayers_used")
    context.bot.send_message(chat_id=CHAT_ID, text=prayer)

def reminder_job(context):
    reminder = rotate_and_log("reminders", "reminders_used")
    context.bot.send_message(chat_id=CHAT_ID, text=reminder)

# --- Seasonal Emojis ---
seasonal_emojis = {
    "Christmas": "🎄✨",
    "New Year": "🎉🥂",
    "Easter": "✝️🌅",
    "Ramadan": "🌙🕌",
    "Thanksgiving": "🦃🍂",
    "Valentine": "❤️🌹"
}

def seasonal_job(context):
    today = datetime.date.today().strftime("%m-%d")
    for event in content.get("seasonal", []):
        if event["date"] == today:
            # Add emoji theme based on keyword in message
            emojis = "✨"
            for keyword, emoji in seasonal_emojis.items():
                if keyword.lower() in event["message"].lower():
                    emojis = emoji
                    break
            message = f"{emojis} {event['message']}"
            context.bot.send_message(chat_id=CHAT_ID, text=message)
            return

# --- Main ---
def main():
    updater = Updater(BOT_TOKEN)
   scheduler = BackgroundScheduler(timezone=pytz.timezone("Africa/Lagos"))

    # Daily rhythm
    scheduler.add_job(good_morning_job, 'cron', hour=4, minute=30, args=[updater.bot])
    scheduler.add_job(verse_of_the_day_job, 'cron', hour=6, minute=0, args=[updater.bot])
    scheduler.add_job(daily_scripture_job, 'cron', hour=7, minute=0, args=[updater.bot])
    scheduler.add_job(trading_job, 'cron', hour=9, minute=0, args=[updater.bot])
    scheduler.add_job(quote_job, 'cron', hour=12, minute=0, args=[updater.bot])
    scheduler.add_job(prayer_job, 'cron', hour=15, minute=0, args=[updater.bot])
    scheduler.add_job(reminder_job, 'cron', hour=18, minute=0, args=[updater.bot])

    # Seasonal check (runs daily at 4:30 AM, overrides Good Morning if matched)
    scheduler.add_job(seasonal_job, 'cron', hour=4, minute=30, args=[updater.bot])

    scheduler.start()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
