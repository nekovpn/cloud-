# cloud/files/telegram_bot.py

import telegram
from telegram.ext import Application, CommandHandler, CallbackContext
import logging
import asyncio # کتابخانه جدید برای اجرای همزمان

# ... بقیه import ها مثل قبل ...
import os
import requests
import base64
from urllib.parse import urlparse, unquote
import concurrent.futures
from app import run_scrape
from sort import run_sort


# --- Configuration ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
# ... بقیه کانفیگ‌ها مثل قبل ...
CHECK_URL = 'http://www.google.com/generate_204'
CHECK_TIMEOUT = 5
SEND_INTERVAL_SECONDS = 3 * 60 * 60 # 3 ساعت
MAX_PROXIES_TO_SEND = 10


# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Health Checker for ShadowSocks ---
# این تابع بدون تغییر باقی می‌ماند
def check_ss_proxy(proxy_url):
    try:
        parsed_url = urlparse(proxy_url)
        user_info_b64 = parsed_url.username
        user_info_b64 += '=' * (-len(user_info_b64) % 4)
        decoded_user_info = base64.b64decode(user_info_b64).decode('utf-8')
        method, password = decoded_user_info.split(':', 1)
        server = parsed_url.hostname
        port = parsed_url.port
        password = unquote(password)
        proxy_dict = {
            'http': f'socks5h://{server}:{port}',
            'https': f'socks5h://{server}:{port}'
        }
        response = requests.get(CHECK_URL, proxies=proxy_dict, timeout=CHECK_TIMEOUT)
        if response.status_code == 204:
            logger.info(f"SUCCESS: Proxy {server}:{port} is working.")
            return proxy_url
        else:
            logger.warning(f"FAILED: Proxy {server}:{port} returned status {response.status_code}.")
            return None
    except Exception as e:
        logger.error(f"FAILED: Proxy {urlparse(proxy_url).hostname}:{urlparse(proxy_url).port} - {e}")
        return None

# --- Main Bot Job ---
# تابع اصلی حالا باید async باشه
async def run_and_send_proxies(context: CallbackContext):
    bot = context.bot
    await bot.send_message(chat_id=CHANNEL_ID, text="🤖 فرآیند جمع‌آوری و تست پراکسی‌ها شروع شد...")
    
    # اجرای توابع سنکرون (معمولی) در یک ترد جداگانه
    await asyncio.to_thread(run_scrape)
    await asyncio.to_thread(run_sort)

    ss_file_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'Splitted-By-Protocol', 'ss.txt'))
    try:
        with open(ss_file_path, 'r', encoding='utf-8') as f:
            ss_proxies = [line.strip() for line in f if line.strip().startswith('ss://')]
    except FileNotFoundError:
        await bot.send_message(chat_id=CHANNEL_ID, text="⚠️ فایل پراکسی‌های شادوساکس پیدا نشد.")
        return

    if not ss_proxies:
        await bot.send_message(chat_id=CHANNEL_ID, text="ℹ️ هیچ پراکسی شادوساکس برای تست پیدا نشد.")
        return
        
    await bot.send_message(chat_id=CHANNEL_ID, text=f"تست {len(ss_proxies)} سرور شادوساکس شروع شد...")

    working_proxies = []
    # اجرای تست‌ها در تردپول
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        loop = asyncio.get_event_loop()
        futures = [loop.run_in_executor(executor, check_ss_proxy, proxy) for proxy in ss_proxies]
        for response in await asyncio.gather(*futures):
            if response:
                working_proxies.append(response)

    if working_proxies:
        message_header = "✅ پراکسی‌های سالم شادوساکس:\n\n"
        await bot.send_message(chat_id=CHANNEL_ID, text=message_header)
        
        for proxy in working_proxies[:MAX_PROXIES_TO_SEND]:
            # برای کپی کردن راحت، از Markdown استفاده می‌کنیم
            await bot.send_message(chat_id=CHANNEL_ID, text=f"`{proxy}`", parse_mode='MarkdownV2')
        
        await bot.send_message(chat_id=CHANNEL_ID, text="🆔 @proxyfig")
        logger.info(f"Sent {len(working_proxies[:MAX_PROXIES_TO_SEND])} working proxies to the channel.")
    else:
        await bot.send_message(chat_id=CHANNEL_ID, text="❌ متاسفانه هیچ پراکسی سالمی پیدا نشد.")
        logger.warning("No working proxies found.")

# --- Command Handlers ---
# این توابع هم باید async باشند
async def start(update, context):
    await update.message.reply_text('سلام! ربات فعال است. برای اجرای دستی از /runnow استفاده کنید.')

async def run_now_command(update, context):
    await update.message.reply_text('باشه، فرآیند را به صورت دستی اجرا می‌کنم...')
    context.job_queue.run_once(run_and_send_proxies, 0)

# --- Main Bot Function ---
def main():
    # ساختار جدید برای راه‌اندازی ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("runnow", run_now_command))

    # زمان‌بندی کار
    job_queue = application.job_queue
    job_queue.run_repeating(run_and_send_proxies, interval=SEND_INTERVAL_SECONDS, first=10)

    # اجرای ربات
    logger.info("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
