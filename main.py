from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))
end_of_year = datetime.date(2026, 3, 21)
emojis_dict = {'1':'1️⃣','2':'2️⃣','3':'3️⃣','4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣','0':'0️⃣'}

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

async def send_daily_message():
    today = datetime.date.today()
    daysleft = ''.join(emojis_dict[i] for i in str((end_of_year - today).days))
    await bot.send_message(chat_id=CHAT_ID, text=f"{daysleft} days left")

# Schedule the job
scheduler.add_job(send_daily_message, 'cron', hour=23, minute=23)

async def main():
    scheduler.start()           # Start scheduler
    print("Bot started. Waiting to send messages...")
    # Wait indefinitely without while True
    await asyncio.Event().wait()

# Start the event loop
asyncio.run(main())

