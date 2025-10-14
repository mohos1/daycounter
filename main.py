from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import os
import asyncio
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))
end_of_year=datetime.date(2026,3,21)
emojis_dict={'1':'1️⃣','2':'2️⃣','3':'3️⃣','4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣','0':'0️⃣'}
bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

async def send_daily_message():
    today = datetime.date.today()
    daysleft=''
    for i in str((end_of_year-today).days):
        daysleft+=emojis_dict[i]
    await bot.send_message(chat_id=CHAT_ID, text=f"{daysleft} days left")

scheduler.add_job(lambda:asyncio.create_task(send_daily_message()), 'cron', hour=6, minute=0)

print("Bot started. Waiting to send messages...")
scheduler.start()
