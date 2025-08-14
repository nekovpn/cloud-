# cloud/files/telegram_bot.py

import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
import requests
import base64
import re
import os
from urllib.parse import urlparse, unquote
import concurrent.futures

# Import functions from your other scripts
from app import run_scrape
from sort import run_sort

# --- Configuration ---
BOT_TOKEN = "7483884524:AAF0PHPQFIoGsSzvodUcUPdGxDHzjIZjW0c"  # توکن ربات خود را اینجا قرار دهید
CHANNEL_ID = "-1002234854094"  # شناسه کانال خود را اینجا قرار دهید (مثال: -100123456789)
CHECK_URL = 'http://www.google.com/generate_204' # URL برای تست اتصال
CHECK_TIMEOUT = 5  # 5 ثانیه برای هر تست
SEND_INTERVAL_SECONDS = 3 * 60 * 60 # 3 ساعت
MAX_PROXIES_TO_SEND = 10

# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Health Checker for ShadowSocks ---
def check_ss_proxy(proxy_url):
    try:
        # Parse ss:// URL
        # ss://method:password@server:port
        parsed_url = urlparse(proxy_url)
        
        # Base64 decode user info part
        user_info_b64 = parsed_url.username
        # Add padding if needed
        user_info_b64 += '=' * (-len(user_info_b64) % 4)
        decoded_user_info = base64.b64decode(user_info_b64).decode('utf-8')
        
        method, password = decoded_user_info.split(':', 1)
        server = parsed_url.hostname
        port = parsed_url.port
        
        # Unquote password just in case
        password = unquote(password)

        proxy_dict = {
            'http': f'socks5://{server}:{port}',
            'https': f'socks5://{server}:{port}'
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
def run_and_send_proxies(context: CallbackContext):
    bot = context.bot
    bot.send_message(chat_id=CHANNEL_ID, text="🤖 فرآیند جمع‌آوری و تست پراکسی‌ها شروع شد...")

    # 1. Scrape, merge, and rename configs
    run_scrape()

    # 2. Sort configs into separate files
    run_sort()

    # 3. Read ShadowSocks configs
    ss_file_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'Splitted-By-Protocol', 'ss.txt'))
    try:
        with open(ss_file_path, 'r', encoding='utf-8') as f:
            ss_proxies = [line.strip() for line in f if line.strip().startswith('ss://')]
    except FileNotFoundError:
        bot.send_message(chat_id=CHANNEL_ID, text="⚠️ فایل پراکسی‌های شادوساکس پیدا نشد. فرآیند متوقف شد.")
        return

    if not ss_proxies:
        bot.send_message(chat_id=CHANNEL_ID, text="ℹ️ هیچ پراکسی شادوساکس برای تست پیدا نشد.")
        return
        
    bot.send_message(chat_id=CHANNEL_ID, text=f"تست {len(ss_proxies)} سرور شادوساکس شروع شد. این مرحله ممکن است چند دقیقه طول بکشد...")

    # 4. Check proxies in parallel
    working_proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_proxy = {executor.submit(check_ss_proxy, proxy): proxy for proxy in ss_proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            result = future.result()
            if result:
                working_proxies.append(result)

    # 5. Send results to channel
    if working_proxies:
        message = "✅ پراکسی‌های سالم شادوساکس:\n\n"
        message += "\n\n".join(working_proxies[:MAX_PROXIES_TO_SEND])
        message += f"\n\n🆔 @proxyfig"
        
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        logger.info(f"Sent {len(working_proxies[:MAX_PROXIES_TO_SEND])} working proxies to the channel.")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text="❌ متاسفانه هیچ پراکسی سالمی پیدا نشد.")
        logger.warning("No working proxies found.")

# --- Command Handlers ---
def start(update, context):
    update.message.reply_text('سلام! ربات فعال است و پراکسی‌ها را به صورت خودکار به کانال ارسال می‌کند. برای اجرای دستی، از دستور /runnow استفاده کنید.')

def run_now_command(update, context):
    update.message.reply_text('باشه، فرآیند را به صورت دستی اجرا می‌کنم...')
    context.job_queue.run_once(run_and_send_proxies, 0)

# --- Main Bot Function ---
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("runnow", run_now_command))

    # Schedule the job
    job_queue.run_repeating(run_and_send_proxies, interval=SEND_INTERVAL_SECONDS, first=10) # 10 ثانیه بعد از اجرا، اولین بار شروع میشه

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started and job scheduled.")
    updater.idle()

if __name__ == '__main__':
    main()
