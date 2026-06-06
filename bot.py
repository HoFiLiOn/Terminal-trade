import asyncio
import sqlite3
import logging
import sys
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
SOURCE_CHANNEL = '@TWSA_HOF'
BOT_NAME = "Vexor Observer"
API_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}"
# ==================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()
    logger.info("База данных готова")

def add_subscriber(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_subscriber(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_subscribers():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM subscribers')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_subscriber_count():
    return len(get_all_subscribers())

# ---------- ПОЛУЧЕНИЕ ПОСТОВ ----------
last_post_id = None

def get_latest_post():
    global last_post_id
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            if messages:
                latest = messages[0]
                current_id = latest.get('id')
                text = latest.get('text', 'Новый пост')
                if isinstance(text, list):
                    text = ' '.join(str(item) for item in text)
                link = f"https://t.me/{SOURCE_CHANNEL[1:]}/{current_id}"
                
                if last_post_id is None:
                    last_post_id = current_id
                    return None
                elif current_id != last_post_id:
                    last_post_id = current_id
                    return {'text': text[:500], 'link': link}
        return None
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None

def get_last_posts(limit=5):
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            result = []
            for msg in messages[:limit]:
                text = msg.get('text', '📷 Медиа')
                if isinstance(text, list):
                    text = ' '.join(str(item) for item in text)
                date = datetime.fromtimestamp(msg.get('date', 0))
                msg_id = msg.get('id')
                link = f"https://t.me/{SOURCE_CHANNEL[1:]}/{msg_id}"
                result.append(f"📌 {date.strftime('%d.%m %H:%M')}\n{text[:300]}\n{link}")
            return result
        return []
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []

# ---------- КНОПКИ ----------
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✅ ПОДПИСАТЬСЯ", callback_data='subscribe'),
            InlineKeyboardButton("❌ ОТПИСАТЬСЯ", callback_data='unsubscribe'),
        ],
        [
            InlineKeyboardButton("📜 ПОСЛЕДНИЕ 5", callback_data='last_5'),
            InlineKeyboardButton("📜 ПОСЛЕДНИЕ 10", callback_data='last_10'),
        ],
        [
            InlineKeyboardButton("📊 СТАТИСТИКА", callback_data='stats'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- ОБРАБОТЧИКИ ----------
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"👁 {BOT_NAME}\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"Я слежу за каналом Vexor cheats | News\n"
        f"и присылаю новые посты.\n\n"
        f"👇 ВЫБЕРИ ДЕЙСТВИЕ:",
        reply_markup=get_main_keyboard()
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    if query.data == 'subscribe':
        add_subscriber(user_id)
        query.edit_message_text(
            f"✅ ПОДПИСАН!\n\n👀 Подписчиков: {get_subscriber_count()}",
            reply_markup=get_main_keyboard()
        )
    
    elif query.data == 'unsubscribe':
        remove_subscriber(user_id)
        query.edit_message_text("❌ ОТПИСАН", reply_markup=get_main_keyboard())
    
    elif query.data == 'stats':
        query.edit_message_text(
            f"📊 СТАТИСТИКА\n\n👀 Подписчиков: {get_subscriber_count()}\n📢 Канал: Vexor cheats | News",
            reply_markup=get_main_keyboard()
        )
    
    elif query.data in ['last_5', 'last_10']:
        n = 5 if query.data == 'last_5' else 10
        query.edit_message_text(f"⏳ Загружаю {n} постов...")
        
        posts = get_last_posts(n)
        if posts:
            text = "\n\n".join(posts)
            query.edit_message_text(text, disable_web_page_preview=True)
        else:
            query.edit_message_text("❌ Ошибка загрузки", reply_markup=get_main_keyboard())

# ---------- МОНИТОРИНГ ----------
def monitor_channel(context: CallbackContext):
    post = get_latest_post()
    if post:
        subscribers = get_all_subscribers()
        for user_id in subscribers:
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔔 НОВЫЙ ПОСТ!\n\n{post['text']}\n\n{post['link']}",
                    disable_web_page_preview=True
                )
                asyncio.sleep(0.05)
            except Exception as e:
                if "Forbidden" in str(e):
                    remove_subscriber(user_id)
                logger.error(f"Ошибка {user_id}: {e}")

# ---------- ЗАПУСК ----------
def main():
    init_db()
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем мониторинг
    job_queue = updater.job_queue
    job_queue.run_repeating(monitor_channel, interval=5, first=1)
    
    logger.info("✅ Бот запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")