# cloud--main/files/send_to_telegram.py

import os
import requests
import base64
import telegram
import logging
from urllib.parse import urlparse, unquote
import concurrent.futures

# --- Configuration from Environment Variables ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
CHECK_URL = 'http://www.google.com/generate_204'
CHECK_TIMEOUT = 5
MAX_PROXIES_TO_SEND = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        proxy_dict = {'http': f'socks5h://{server}:{port}', 'https': f'socks5h://{server}:{port}'}
        response = requests.get(CHECK_URL, proxies=proxy_dict, timeout=CHECK_TIMEOUT)
        if response.status_code == 204:
            logger.info(f"SUCCESS: Proxy {server}:{port} is working.")
            return proxy_url
        return None
    except Exception:
        return None

def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set as environment variables.")
        return

    bot = telegram.Bot(token=BOT_TOKEN)
    logger.info("Bot instance created.")
    
    ss_file_path = os.path.abspath(os.path.join(os.getcwd(), 'Splitted-By-Protocol', 'ss.txt'))
    
    try:
        with open(ss_file_path, 'r', encoding='utf-8') as f:
            ss_proxies = [line.strip() for line in f if line.strip().startswith('ss://')]
    except FileNotFoundError:
        bot.send_message(chat_id=CHANNEL_ID, text="⚠️ فایل پراکسی‌های شادوساکس پیدا نشد.")
        return

    if not ss_proxies:
        bot.send_message(chat_id=CHANNEL_ID, text="ℹ️ پراکسی شادوساکس برای تست پیدا نشد.")
        return

    bot.send_message(chat_id=CHANNEL_ID, text=f"✅ در حال تست {len(ss_proxies)} سرور شادوساکس...")
    
    working_proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_ss_proxy, proxy) for proxy in ss_proxies]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                working_proxies.append(result)

    if working_proxies:
        message = "✅ ۱۰ پراکسی سالم شادوساکس:\n\n"
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        for proxy in working_proxies[:MAX_PROXIES_TO_SEND]:
            # برای کلیک‌پذیر شدن، پراکسی را در تگ کد قرار می‌دهیم
            bot.send_message(chat_id=CHANNEL_ID, text=f"`{proxy}`", parse_mode='MarkdownV2')
        
        bot.send_message(chat_id=CHANNEL_ID, text="🆔 @proxyfig")
        logger.info(f"Sent {len(working_proxies[:MAX_PROXIES_TO_SEND])} proxies.")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text="❌ هیچ پراکسی سالمی پیدا نشد.")
        logger.warning("No working proxies found.")

if __name__ == '__main__':
    main()
