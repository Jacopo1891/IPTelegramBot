from functools import wraps
import logging, requests
import speedtest
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from lexicon.providers.ovh import Provider

from config import *

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

reply_keyboard = [
    ["What's my ip?", "What's my VPN's ip?"],
    ["Who's at home?", "Speed test"]
]

markup = ReplyKeyboardMarkup(reply_keyboard)

CHOOSING = range(1)

def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in allowedChats:
            logger.info(f"Unauthorize user try to use me! {update.effective_user}")
            await update.message.reply_text("I think <a href='https://en.wikiquote.org/wiki/Time'>this</a> is what you are looking for!", parse_mode='HTML', disable_web_page_preview=True,reply_markup=markup)
            return
        return await func(update, context, *args, **kwargs)    
    return wrapped

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Welcome! What do you need?",reply_markup=markup)
    return CHOOSING

@restricted
async def ip_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"This is my ip: {getIp()}.",reply_markup=markup)
    return CHOOSING

@restricted
async def vpn_ip_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"This is VPN's ip: {getVPNIp()}.",reply_markup=markup)
    return CHOOSING

@restricted
async def whoIsAtHome_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"I'm not ready for this!",reply_markup=markup)
    return CHOOSING     

@restricted
async def speedtest_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Let me work...", parse_mode='HTML', disable_web_page_preview=True,reply_markup=markup)
    speedtest = getConnectionSpeed()
    download = "Download: {:.2f} Mb/s".format(speedtest[0] / (1024*1024))
    upload = "\nUpload: {:.2f} Mb/s".format(speedtest[1] / (1024*1024))
    ping = "\nPing: {:.2f}".format(speedtest[2])
    await update.message.reply_text(download + upload + ping, parse_mode='HTML', disable_web_page_preview=True,reply_markup=markup)
    return CHOOSING

async def random_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("I think <a href='https://google.com'>this</a> is what you are looking for!", parse_mode='HTML', disable_web_page_preview=True,reply_markup=markup)
    return CHOOSING

def getIp():
    url = "https://ifconfig.me/"
    return requests.get(url).text.strip()

def getVPNIp():
    provider = Provider(lexiconConfig)
    provider.authenticate()

    record_ip_address_response = provider.list_records(name=vpnUrl)
    return record_ip_address_response[0]["content"]   

def getConnectionSpeed():
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    s.download()
    s.upload()   
    res = s.results.dict()
    return res["download"], res["upload"], res["ping"]

def main() -> None:
    if(botId == "" or not allowedChats):
        logger.error("Bot id or allowed chat are missing.")
        return

    application = Application.builder().token(botId).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^(What's my ip\?)$"), ip_choice),
                MessageHandler(filters.Regex("^(What's my VPN's ip\?)$"), vpn_ip_choice),
                MessageHandler(filters.Regex("^(Who's at home\?)$"), whoIsAtHome_choice),
                MessageHandler(filters.Regex("^(Speed test)$"), speedtest_choice),
                MessageHandler(filters.Regex("(.*?)"), random_choice),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Stop$"), None)],
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()