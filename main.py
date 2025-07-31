import os
import time
from datetime import datetime, time as dt_time
from instagrapi import Client
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
CHECK_INTERVAL = 86400  # 24 часа

instagram_client = Client()
telegram_bot = TeleBot(TELEGRAM_BOT_TOKEN)

current_followers = set()
previous_followers = set()


def login_to_instagram():
    try:
        # Попытка входа
        instagram_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("✅ Успешный вход в Instagram")
    except Exception as e:
        # Если требуется 2FA
        if "two-factor" in str(e):
            print("🔐 Требуется двухфакторная аутентификация (2FA)")
            verification_code = input("Введите код из SMS/приложения: ")
            instagram_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, verification_code=verification_code)
            print("✅ Вход с 2FA выполнен")
        else:
            print(f"❌ Ошибка входа в Instagram: {e}")
            raise

def get_followers():
    try:
        user_id = instagram_client.user_id_from_username(INSTAGRAM_USERNAME)
        followers = instagram_client.user_followers(user_id)
        return {str(user.pk) for user in followers.values()}
    except Exception as e:
        print(f"❌ Ошибка получения подписчиков: {e}")
        return None


def send_telegram_message(message):
    try:
        telegram_bot.send_message(TELEGRAM_CHANNEL_ID, message)
        print("✉️ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")


def check_unfollowers():
    global current_followers, previous_followers
    current_followers = get_followers()
    if not current_followers:
        return

    if previous_followers:
        unfollowers = previous_followers - current_followers
        if unfollowers:
            message = "🔔 Отписались от вашего профиля:\n\n"
            for user_id in unfollowers:
                user_info = instagram_client.user_info(user_id)
                message += f"• @{user_info.username} ({user_info.full_name})\n"
            send_telegram_message(message)
        else:
            print(f"{datetime.now()}: Никто не отписался")

    previous_followers = current_followers.copy()


def run_daily_check():
    login_to_instagram()
    global previous_followers
    previous_followers = get_followers()
    if not previous_followers:
        return

    print("🟢 Бот запущен. Ожидание ежедневной проверки...")
    while True:
        now = datetime.now()
        target_time = dt_time(9, 0)  # Проверка в 9:00 утра
        if now.time() >= target_time:
            check_unfollowers()
            time.sleep(CHECK_INTERVAL)
        else:
            time.sleep(60)


if __name__ == "__main__":
    try:
        run_daily_check()
    except KeyboardInterrupt:
        print("⛔ Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
