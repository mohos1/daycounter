from telegram import Bot,BotCommand,Update
from telegram.ext import CommandHandler,ApplicationBuilder,filters,PicklePersistence,MessageHandler
import datetime
import os
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDate
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from uuid import uuid4
import logging
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
    def remove_counter(self,name,scheduler):
        scheduler.remove_job(str(self.counters[name].id))
        del self.counters[name]
    def build_counter(self,name,scheduler,bot):
        counter=self.counters[name]
        scheduler.add_job(send_daily_message,'cron',args=[self.chatid,counter.deadline,bot],id=str(counter.id)
                        ,hour=counter.sendtime[0],minute=counter.sendtime[1],end_date=counter.deadline)
class Flags:
    def __init__(self) -> None:
        self.name=False
        self.deadline=False
        self.sendtime=False
        self.remove=False
        self.cwo=None

async def send_daily_message(chatid,deadline,bot):
    numicons={'0':'0️⃣','1':'1️⃣','2':'2️⃣','3':'3️⃣','4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣'}
    today = datetime.date.today()
    daysleft=''.join(numicons[i] for i in str((deadline-today).days)[::-1])
    message=f'{daysleft} روز مانده'
    await bot.send_message(chat_id=chatid, text=message)

async def startup(app):
    users_data=await app.persistence.get_user_data()
    for userkey in users_data:
        user=app.user_data[userkey]['user']
        for counterkey in user.counters:
            user.build_counter(counterkey,asyncscheduler,app.bot)
    commands=[
        BotCommand('start','شروع ربات'),
        BotCommand('help','نمایش همه ی دستور ها'),
        BotCommand('newcounter','اضافه کردن شمارنده'),
        BotCommand('removecounter','حذف شمارنده')
    ]
    await app.bot.set_my_commands(commands)
    asyncscheduler.start()
    print("Bot started. Waiting to send messages...")

async def user_init(update,context):
    chatid=update.effective_chat.id
    context.user_data['user']=context.user_data.get('user',User(chatid))
    context.user_data['flags']=Flags()
    await context.bot.send_message(chat_id=chatid,text='سلام به روز شمار خوش آمدید')

async def help(update,context):
    commands=await context.bot.get_my_commands()
    maxlen=max([len(s.command) for s in commands])
    message='دستور های قابل دسترس\n\n'
    for c in commands:
        message+=f'{c.command:<{maxlen}} - {c.description}\n'
    await update.message.reply_text(message)


async def add_counter_interface(update,context):
    context.user_data['flags']=Flags()
    await update.message.reply_text('لطفا نام شمارنده را وارد کنید')
    context.user_data['flags'].name=True

async def manager(update,context):
    if context.user_data['flags'].name:
        await get_counter_name(update,context)
    elif context.user_data['flags'].deadline:
        await get_counter_deadline(update,context)
    elif context.user_data['flags'].sendtime:
        await get_counter_sendtime(update,context)
    elif context.user_data['flags'].remove:
        await rm_counter_identifier(update,context)

async def get_counter_name(update,context):
    name=update.message.text
    if not(name in context.user_data['user'].counters):
        context.user_data['user'].add_counter(name)
        context.user_data['flags'].name=False
        context.user_data['flags'].deadline=True
        context.user_data['flags'].cwo=name
        await update.message.reply_text('لطفا تاریخ ضرب الاجل را به شکل \n روز/ماه/سال وارد کنید')
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
    if 0<=hour<24 and 0<=minute<60:
        context.user_data['user'].counters[context.user_data['flags'].cwo].sendtime=(hour,minute)
        context.user_data['flags'].sendtime=False
        context.user_data['user'].build_counter(context.user_data['flags'].cwo,asyncscheduler,application.bot)
        context.user_data['flags'].cwo=None
        await update.message.reply_text('شمارنده با موفقیت اضافه شد')
    else:
        await update.message.reply_text('لطفا  ساعتی معتبر وارد کنید')

async def rm_counter_interface(update,context):
    context.user_data['flags']=Flags()
    context.user_data['flags'].remove=True
    await update.message.reply_text('لطفا نام شمارنده ی مورد نظر را وارد کنید')

async def rm_counter_identifier(update,context):
    name=update.message.text
    if name in context.user_data['user'].counters:
        context.user_data['user'].remove_counter(name,asyncscheduler)
        await update.message.reply_text('شمارنده با موفقیت حذف شد')
    else:
        await update.message.reply_text('شمارنده ای با این نام وجود ندارد')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
DATABASE_PATH=str(os.getenv('DATABASE_PATH'))

persistence=PicklePersistence(DATABASE_PATH)
application=ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).post_init(startup).build()   

bottimezone=datetime.timezone(datetime.timedelta(hours=3,minutes=30))
asyncscheduler = AsyncIOScheduler(timezone=bottimezone)

init_handler=CommandHandler('start',user_init)
add_counter_handler=CommandHandler('newcounter',add_counter_interface)
remove_counter_handler=CommandHandler('removecounter',rm_counter_interface)
manager_handler=MessageHandler(filters.TEXT & ~filters.COMMAND,manager)
help_handler=CommandHandler('help',help)

application.add_handler(init_handler)
application.add_handler(add_counter_handler)
application.add_handler(manager_handler)
application.add_handler(remove_counter_handler)
application.add_handler(help_handler)

application.run_polling()
