# cloud--main/files/generate_and_send_links.py

import os
import telegram
import logging

# --- Configuration from Environment Variables ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
GITHUB_REPO_URL = os.environ.get("GITHUB_REPOSITORY") # Automatically set by GitHub Actions
GITHUB_BRANCH = "main" # نام برنچ اصلی شما

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if not BOT_TOKEN or not CHANNEL_ID or not GITHUB_REPO_URL:
        logger.error("Error: Required environment variables are not set.")
        return

    bot = telegram.Bot(token=BOT_TOKEN)
    logger.info("Bot instance created.")

    # Base URL for raw GitHub content
    raw_base_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_URL}/{GITHUB_BRANCH}"

    # Subscription links for each protocol
    sub_links = {
        "VLESS": f"{raw_base_url}/Splitted-By-Protocol/vless.txt",
        "VMess": f"{raw_base_url}/Splitted-By-Protocol/vmess.txt",
        "Trojan": f"{raw_base_url}/Splitted-By-Protocol/trojan.txt",
        "ShadowSocks (SS)": f"{raw_base_url}/Splitted-By-Protocol/ss.txt",
        "All (Base64)": f"{raw_base_url}/All_Configs_Base64.txt"
    }

    message = "✅ **لینک‌های سابسکریپشن جدید به‌روزرسانی شد**\n\n"
    message += "لینک‌ها را کپی کرده و در کلاینت خود وارد کنید:\n\n"

    for name, link in sub_links.items():
        message += f"🔗 **{name}**:\n`{link}`\n\n"

    message += "🆔 @proxyfig"

    try:
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        logger.info("Successfully sent subscription links to the channel.")
    except Exception as e:
        logger.error(f"Failed to send message to Telegram: {e}")

if __name__ == '__main__':
    main()
