from telegram import Bot
from telegram.ext import CommandHandler,ApplicationBuilder,filters,PicklePersistence,MessageHandler
import datetime
import os
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDate
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from uuid import uuid4
class Counter:
    def __init__(self,sendtime=None,deadline=None) -> None:
        self.sendtime=sendtime
        self.deadline=deadline
        self.id=uuid4()
class User:
    def __init__(self,chatid) -> None:
        self.chatid=chatid
        self.counters={}
    def add_counter(self,name,sendtime=None,deadline=None):
        self.counters[name]=Counter(sendtime,deadline)
    def remove_counter(self):
        pass
    def build_counter(self,counter,scheduler):
        scheduler.add_job(send_daily_message,
                        'cron',args=[self.chatid,counter.deadline],id=str(counter.id)
                        ,hour=counter.sendtime[0],minute=counter.sendtime[1],end_date=counter.deadline)
class Flags:
    def __init__(self) -> None:
        self.name=False
        self.deadline=False
        self.sendtime=False
        self.cwo=None

async def send_daily_message(chatid,deadline):
    today = datetime.date.today()
    daysleft=(deadline-today).days
    message=f'{daysleft} روز مانده'
    await bot.send_message(chat_id=chatid, text=message)

async def startup(app):
    asyncscheduler.start()
    print("Bot started. Waiting to send messages...")

async def init(update,context):
    chatid=update.effective_chat.id
    context.user_data['user']=context.user_data.get('user',User(chatid))
    context.user_data['flags']=context.user_data.get('flags',Flags())
    print(context.user_data)
    await context.bot.send_message(chat_id=chatid,text='سلام به روز شمار خوش آمدید')

async def add_counter(update,context):
    await update.message.reply_text('لطفا نام شمارنده را وارد کنید')
    context.user_data['flags'].name=True

async def manager(update,context):
    if context.user_data['flags'].name:
        await get_counter_name(update,context)
    elif context.user_data['flags'].deadline:
        await get_counter_deadline(update,context)
    elif context.user_data['flags'].sendtime:
        await get_counter_sendtime(update,context)

async def get_counter_name(update,context):
    name=update.message.text
    if not(name in context.user_data['user'].counters):
        context.user_data['user'].add_counter(name)
        context.user_data['flags'].name=False
        await update.message.reply_text('لطفا تاریخ ضرب الاجل را به شکل \n روز/ماه/سال وارد کنید')
        context.user_data['flags'].deadline=True
        context.user_data['flags'].cwo=name
    else:
        await update.message.reply_text('لطفا نام دیگری انتخاب کنید این نام تکراری است')

async def get_counter_deadline(update,context):
    rawdate=[int(i) for i in update.message.text.split('/')]
    try:
        deadlinedate=JalaliDate(rawdate[0],rawdate[1],rawdate[2]).to_gregorian()
    except:
        await update.message.reply_text('لطفا یک تاریخ معتبر وارد کنید')
        return -1
    today=datetime.datetime.date(datetime.datetime.today())
    if (deadlinedate-today).days>0:
        context.user_data['user'].counters[context.user_data['flags'].cwo].deadline=deadlinedate
        context.user_data['flags'].deadline=False
        context.user_data['flags'].sendtime=True
        await update.message.reply_text('لطفا ساعت ارسال پیام را به شکل\n دقیقه:ساعت وارد کنید')
    else:
        await update.message.reply_text('لطفا یک تاریخ معتبر وارد کنید')

async def get_counter_sendtime(update,context):
    rawdata=update.message.text.split(':')
    try:
        hour,minute=int(rawdata[0]),int(rawdata[1])
    except:
        await update.message.reply_text('لطفا  ساعتی معتبر وارد کنید')
        return -1
    if 0<hour<24 and 0<minute<60:
        context.user_data['user'].counters[context.user_data['flags'].cwo].sendtime=(hour,minute)
        context.user_data['flags'].sendtime=False
        context.user_data['user'].build_counter(context.user_data['user'].counters[context.user_data['flags'].cwo],asyncscheduler)
    else:
        await update.message.reply_text('لطفا  ساعتی معتبر وارد کنید')




load_dotenv()
BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
DATABASE_PATH=str(os.getenv('DATABASE_PATH'))
persistence=PicklePersistence(DATABASE_PATH)
application=ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).post_init(startup).build()
bot = Bot(token=BOT_TOKEN)
bottimezone=datetime.timezone(datetime.timedelta(hours=3,minutes=30))
asyncscheduler = AsyncIOScheduler(timezone=bottimezone)


init_handler=CommandHandler('start',init)
add_counter_handler=CommandHandler('newcounter',add_counter)
manager_handler=MessageHandler(filters.TEXT & ~filters.COMMAND,manager)

application.add_handlers([init_handler,add_counter_handler,manager_handler])

application.run_polling()
