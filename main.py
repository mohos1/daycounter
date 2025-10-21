from telegram import Bot,BotCommand,Update
from telegram.ext import CommandHandler,ApplicationBuilder,filters,PicklePersistence,MessageHandler
import datetime
import os
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDate
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from uuid import uuid4
import logging
from functools import wraps
class Counter:
    def __init__(self,sendtime,deadline,chatname,chattype,chatid) -> None:
        self.sendtime=sendtime
        self.deadline=deadline
        self.chatname=chatname
        self.chattype=chattype
        self.chatid=chatid
        self.id=str(uuid4())
class User:
    def __init__(self) -> None:
        self.counters={}
    def add_counter(self,name,chatname,chattype,chatid,sendtime,deadline,scheduler,bot):
        self.counters[name]=Counter(sendtime,deadline,chatname,chattype,chatid)
        counter=self.counters[name]
        scheduler.add_job(send_daily_message,'cron',args=[counter.chatid,counter.deadline,bot],id=counter.id
                        ,hour=counter.sendtime[0],minute=counter.sendtime[1],end_date=counter.deadline)
    def remove_counter(self,name,scheduler):
        scheduler.remove_job(str(self.counters[name].id))
        self.counters.pop(name)
class Flags:
    def __init__(self) -> None:
        self.name=False
        self.deadline=False
        self.sendtime=False
        self.remove=False

def user_init_checker(func):
    @wraps(func)
    async def wrapper(*args,**kwargs):
        if is_user_initialized(args[1].user_data):
            await func(*args,**kwargs)
        else:
            await args[0].message.reply_text('لطفا نخست ربات را با /start شروع کنید')
    return wrapper



async def send_daily_message(chatid,deadline,bot):
    numicons={'0':'0️⃣','1':'1️⃣','2':'2️⃣','3':'3️⃣','4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣'}
    today = datetime.date.today()
    daysleft=''.join(numicons[i] for i in str((deadline-today).days))
    message=f'روز مانده'
    try:
        await bot.send_message(chat_id=chatid, text=daysleft)
        await bot.send_message(chat_id=chatid,text=message)
    except:
        await send_daily_message(chatid,deadline,bot)

async def user_init(update,context):
    chatid=update.effective_chat.id
    context.user_data['user']=context.user_data.get('user',User())
    context.user_data['flags']=context.user_data.get('flags',Flags())
    context.user_data['temp']=context.user_data.get('temp',dict())
    await context.bot.send_message(chat_id=chatid,text='سلام به روز شمار خوش آمدید')

def is_user_initialized(user_data):
    if user_data.get('user')==None or user_data.get('flags')==None or user_data.get('temp')==None:
        return False
    return True

@user_init_checker
async def help(update,context):
    commands=await context.bot.get_my_commands()
    mlen=max([len(i.command) for i in commands])
    message='```\nدستورهای قابل دسترس\n\n'
    for c in commands:
        message+=f'{c.command:<{mlen}}  |  {c.description}\n'
    message+='```'
    await update.message.reply_text(message,parse_mode='MarkdownV2')

@user_init_checker
async def list_counters(update,context):
    message='```\nفهرست شمارنده ها \n\n'
    userobj=context.user_data['user']
    if len(userobj.counters):
        mlen=max(len(i) for i in userobj.counters)
    empty=0
    for counterkey in userobj.counters:
        counter=userobj.counters[counterkey]
        if update.effective_chat.type=='private':
            empty=1
            message+=f'{counterkey:<{mlen}}  |  {counter.sendtime[0]:02d}:{counter.sendtime[1]:02d}  |  {JalaliDate(counter.deadline)}  |  {counter.chattype:<7}  |  {counter.chatname}\n'
        elif counter.chatname==update.effective_chat.title:
            empty=1
            message+=f'{counterkey:<{mlen}}  |  {counter.sendtime[0]:02d}:{counter.sendtime[1]:02d}  |  {JalaliDate(counter.deadline)}  |  {counter.chattype:<7}  |  {counter.chatname}\n'
    message+='```'
    if empty:
        await update.message.reply_text(message,parse_mode='MarkdownV2')
    else:
        await update.message.reply_text('شمارنده ای وجود ندارد')


@user_init_checker
async def add_counter_interface(update,context):
    await update.message.reply_text('لطفا نام شمارنده را وارد کنید')
    context.user_data['flags'].name=True

@user_init_checker
async def manager_interface(update,context):
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
    if not(counter_name_validator(name,context.user_data['user'].counters)):
        chatname=update.effective_user.full_name if update.effective_chat.type=='private' else update.effective_chat.title
        context.user_data['temp']={'name':name,'chatname':chatname,'chattype':update.effective_chat.type,'chatid':update.effective_chat.id}
        context.user_data['flags'].name=False
        context.user_data['flags'].deadline=True
        await update.message.reply_text('لطفا تاریخ ضرب الاجل را به شکل \n روز/ماه/سال وارد کنید')
    else:
        await update.message.reply_text('لطفا نام دیگری انتخاب کنید این نام تکراری است')

def counter_name_validator(name,seq):
    return True if name in seq else False

async def get_counter_deadline(update,context):
    today=datetime.datetime.date(datetime.datetime.today())
    text=update.message.text
    f,deadlinedate=date_validator(text,today)
    if f:
        context.user_data['temp']['deadline']=deadlinedate
        context.user_data['flags'].deadline=False
        context.user_data['flags'].sendtime=True
        await update.message.reply_text('لطفا ساعت ارسال پیام را به شکل\n دقیقه:ساعت وارد کنید')
    else:
        await update.message.reply_text('لطفا یک تاریخ معتبر وارد کنید')

def date_validator(text,basedate=None):
    try:
        rawdate=[int(i) for i in text.split('/')]
        deadlinedate=JalaliDate(rawdate[0],rawdate[1],rawdate[2]).to_gregorian()
        if basedate:
            return (True,deadlinedate) if (deadlinedate-basedate).days>0 else (False,None)
        return (True,deadlinedate)
    except:
        return (False,None)

async def get_counter_sendtime(update,context):
    f,time=time_validator(update.message.text)
    if f:
        context.user_data['temp']['sendtime']=time
        context.user_data['flags'].sendtime=False
        counterparams=context.user_data['temp']
        context.user_data['user'].add_counter(counterparams['name'],counterparams['chatname'],counterparams['chattype'],counterparams['chatid'],counterparams['sendtime'],counterparams['deadline'],asyncscheduler,application.bot)
        await update.message.reply_text('شمارنده با موفقیت اضافه شد')
    else:
        await update.message.reply_text('لطفا  ساعتی معتبر وارد کنید')

def time_validator(text):
    try:
        time=tuple(int(i) for i in text.split(':'))
        if 0<=time[0]<24 and 0<=time[1]<60:
            return (True,time)
        return (False,None)
    except:
        return (False,None)
@user_init_checker
async def rm_counter_interface(update,context):
    context.user_data['flags'].remove=True
    await update.message.reply_text('لطفا نام شمارنده ی مورد نظر را وارد کنید')

async def rm_counter_identifier(update,context):
    name=update.message.text
    if counter_name_validator(name,context.user_data['user'].counters):
        context.user_data['user'].remove_counter(name,asyncscheduler)
        context.user_data['flags'].remove=False
        await update.message.reply_text('شمارنده با موفقیت حذف شد')
    else:
        await update.message.reply_text('شمارنده ای با این نام وجود ندارد')

@user_init_checker
async def cancel(update,context):
    context.user_data['flags']=Flags()
    context.user_data['temp']=dict()
    update.message.reply_text('با موفقیت از دستور خارج شد')

async def startup(app):
    users_data=await app.persistence.get_user_data()
    for userkey in users_data:
        user=users_data[userkey]['user']
        for counterkey in user.counters:
            counter=user.counters[counterkey]
            user.add_counter(counterkey,counter.chatname,counter.chattype,counter.chatid,counter.sendtime,counter.deadline,asyncscheduler,application.bot)
    commands=[
        BotCommand('start','شروع ربات'),
        BotCommand('help','نمایش همه ی دستور ها'),
        BotCommand('add','اضافه کردن شمارنده'),
        BotCommand('remove','حذف شمارنده'),
        BotCommand('list','نمایش تمام شمارنده ها'),
        BotCommand('cancel','خروج از دستور قبلی')
    ]
    await app.bot.set_my_commands(commands)
    asyncscheduler.start()

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
add_counter_handler=CommandHandler('add',add_counter_interface)
remove_counter_handler=CommandHandler('remove',rm_counter_interface)
manager_handler=MessageHandler(filters.TEXT & ~filters.COMMAND,manager_interface)
help_handler=CommandHandler('help',help)
list_handler=CommandHandler('list',list_counters)
cancel_handler=CommandHandler('cancel',cancel)

application.add_handler(init_handler)
application.add_handler(add_counter_handler)
application.add_handler(manager_handler)
application.add_handler(remove_counter_handler)
application.add_handler(help_handler)
application.add_handler(list_handler)
application.add_handler(cancel_handler)

application.run_polling()
