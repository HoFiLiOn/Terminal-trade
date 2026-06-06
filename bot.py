import sqlite3
import logging
import sys
import requests
import threading
import time
from datetime import datetime, timedelta
import telebot
from telebot import types

# ========== конфиг ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
ADMIN_ID = 8388843828
SOURCE_CHANNEL = '@TWSA_HOF'
BOT_NAME = "Vexor Observer"
API_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}"
CHANNEL_INFO_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}/info"
# ============================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
last_post_id = None
bot_start_time = datetime.now()
last_check_time = None
api_status = "проверяется"

# ---------- база данных ----------
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT, first_post_sent INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, posts_received INTEGER DEFAULT 0, posts_opened INTEGER DEFAULT 0, last_activity TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (user_id INTEGER PRIMARY KEY, autounsubscribe INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_subscriber(user_id, username):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO subscribers (user_id, username, join_date, first_post_sent) VALUES (?, ?, ?, 0)', 
              (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute('INSERT OR IGNORE INTO user_stats (user_id, posts_received, posts_opened, last_activity) VALUES (?, 0, 0, ?)',
              (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute('INSERT OR IGNORE INTO user_settings (user_id, autounsubscribe) VALUES (?, 1)',
              (user_id,))
    conn.commit()
    conn.close()

def remove_subscriber(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
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
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM subscribers')
    count = c.fetchone()[0]
    conn.close()
    return count

def update_post_received(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('UPDATE user_stats SET posts_received = posts_received + 1, last_activity = ? WHERE user_id = ?',
              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def update_post_opened(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('UPDATE user_stats SET posts_opened = posts_opened + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT posts_received, posts_opened FROM user_stats WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0)

def mark_first_post_sent(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('UPDATE subscribers SET first_post_sent = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def was_first_post_sent(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT first_post_sent FROM subscribers WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def get_autounsubscribe_setting(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT autounsubscribe FROM user_settings WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 1

def update_last_activity(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('UPDATE user_stats SET last_activity = ? WHERE user_id = ?',
              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def get_inactive_users(days=7):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        SELECT s.user_id FROM subscribers s
        JOIN user_stats us ON s.user_id = us.user_id
        JOIN user_settings uset ON s.user_id = uset.user_id
        WHERE us.last_activity < ? AND uset.autounsubscribe = 1
    ''', (cutoff,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ---------- получение постов из канала ----------
def get_channel_posts(limit=10):
    global api_status
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            api_status = "работает"
            data = response.json()
            messages = data.get('messages', [])
            posts = []
            for msg in messages[:limit]:
                text = msg.get('text', '📷 Медиа')
                if isinstance(text, list):
                    text = ' '.join(str(item) for item in text)
                date = datetime.fromtimestamp(msg.get('date', 0))
                msg_id = msg.get('id')
                link = f"https://t.me/{SOURCE_CHANNEL[1:]}/{msg_id}"
                posts.append({
                    'id': msg_id,
                    'text': text,
                    'date': date,
                    'link': link
                })
            return posts
        else:
            api_status = f"ошибка {response.status_code}"
            return []
    except Exception as e:
        api_status = f"недоступен"
        logger.error(f"Ошибка API: {e}")
        return []

def get_channel_info():
    try:
        response = requests.get(CHANNEL_INFO_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', 'Нет данных'),
                'username': data.get('username', SOURCE_CHANNEL[1:]),
                'description': data.get('description', 'Нет описания'),
                'participants_count': data.get('participants_count', '?'),
                'messages_count': len(data.get('messages', [])),
                'photo': data.get('photo', None)
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка получения инфо канала: {e}")
        return None

def check_new_post():
    global last_post_id, last_check_time
    last_check_time = datetime.now()
    posts = get_channel_posts(limit=1)
    if posts:
        latest = posts[0]
        if last_post_id is None:
            last_post_id = latest['id']
            return None
        elif latest['id'] != last_post_id:
            last_post_id = latest['id']
            return latest
    return None

# ---------- рассылка с кнопками ----------
def send_to_subscribers(post_text, post_link, post_id=None):
    subscribers = get_all_subscribers()
    if not subscribers:
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_open = types.InlineKeyboardButton("📖 Открыть пост", url=post_link)
    btn_unsub = types.InlineKeyboardButton("❌ Отписаться", callback_data='quick_unsubscribe')
    btn_share = types.InlineKeyboardButton("📤 Поделиться", switch_inline_query=f"{post_text[:100]}")
    keyboard.add(btn_open, btn_unsub)
    keyboard.add(btn_share)
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"🔔 Новый пост в канале!\n\n{post_text[:500]}\n\n{post_link}",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            update_post_received(user_id)
            success += 1
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    logger.info(f"Рассылка: {success}/{len(subscribers)}")

def send_first_post(user_id):
    posts = get_channel_posts(limit=1)
    if posts:
        post = posts[0]
        keyboard = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("📖 Открыть пост", url=post['link'])
        keyboard.add(btn)
        bot.send_message(
            user_id,
            f"🎉 Добро пожаловать!\n\nЭто последний пост из канала:\n\n{post['text'][:300]}\n\nСледующие посты будут приходить автоматически.",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        mark_first_post_sent(user_id)

# ---------- проверка неактивных ----------
def check_inactive_users():
    inactive = get_inactive_users(days=7)
    for user_id in inactive:
        try:
            bot.send_message(
                user_id,
                "👋 Ты давно не открывал мои сообщения. Если интерес пропал — отпишись командой /unsubscribe, чтобы не получать уведомления."
            )
        except:
            remove_subscriber(user_id)

# ---------- команда /status ----------
@bot.message_handler(commands=['status'])
def status_command(message):
    uptime = datetime.now() - bot_start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    delay = "неизвестно"
    if last_check_time:
        delay_seconds = (datetime.now() - last_check_time).seconds
        delay = f"{delay_seconds} сек"
    
    text = f"""🤖 Статус бота: онлайн
📡 API ({SOURCE_CHANNEL}): {api_status}
👥 Подписчиков: {get_subscriber_count()}
🕐 Работает: {uptime.days}д {hours}ч {minutes}м
🔄 Последняя проверка: {delay}
⏱ Запущен: {bot_start_time.strftime('%d.%m.%Y %H:%M:%S')}

Последний пост в канале: {last_post_id or 'ещё не проверяли'}"""
    
    bot.reply_to(message, text)

# ---------- команда /channel ----------
@bot.message_handler(commands=['channel'])
def channel_info_command(message):
    bot.send_message(message.chat.id, "📊 Загружаю информацию о канале...")
    
    info = get_channel_info()
    if info:
        text = f"""📢 Информация о канале

📛 Название: {info['title']}
🔗 Ссылка: @{info['username']}
👥 Подписчиков: {info['participants_count']}
📝 Постов: {info['messages_count']}
ℹ️ Описание: {info['description'][:200]}

Бот следит за этим каналом и присылает новые посты подписчикам."""
        
        bot.send_message(message.chat.id, text, disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "❌ Не удалось получить информацию о канале")

# ---------- команда /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ Подписаться", callback_data='subscribe')
    btn2 = types.InlineKeyboardButton("📊 Статус", callback_data='status')
    btn3 = types.InlineKeyboardButton("📢 О канале", callback_data='channel')
    btn4 = types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe')
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    
    bot.send_message(
        message.chat.id,
        f"👁 {BOT_NAME}\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"Я слежу за каналом {SOURCE_CHANNEL}\n"
        f"Новые посты приходят автоматически.\n\n"
        f"👇 Выбери действие:",
        reply_markup=keyboard
    )

# ---------- команда /subscribe ----------
@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_username"
    add_subscriber(user_id, username)
    bot.reply_to(message, f"✅ Подписан!\n👀 Подписчиков: {get_subscriber_count()}")
    send_first_post(user_id)

# ---------- команда /unsubscribe ----------
@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    user_id = message.from_user.id
    remove_subscriber(user_id)
    bot.reply_to(message, "❌ Отписан")

# ---------- обработка callback'ов ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == 'subscribe':
        username = call.from_user.username or "без_username"
        add_subscriber(user_id, username)
        bot.answer_callback_query(call.id, "Подписал!")
        bot.edit_message_text(
            f"✅ Подписан!\n👀 Подписчиков: {get_subscriber_count()}",
            call.message.chat.id,
            call.message.message_id
        )
        send_first_post(user_id)
    
    elif call.data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.answer_callback_query(call.id, "Отписал!")
        bot.edit_message_text("❌ Отписан", call.message.chat.id, call.message.message_id)
    
    elif call.data == 'status':
        uptime = datetime.now() - bot_start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        text = f"""🤖 Статус бота: онлайн
📡 API: {api_status}
👥 Подписчиков: {get_subscriber_count()}
🕐 Работает: {uptime.days}д {hours}ч {minutes}м"""
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    elif call.data == 'channel':
        bot.answer_callback_query(call.id, "Загружаю...")
        info = get_channel_info()
        if info:
            text = f"""📢 {info['title']}
👥 Подписчиков: {info['participants_count']}
📝 Постов: {info['messages_count']}
{info['description'][:200]}"""
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, disable_web_page_preview=True)
        else:
            bot.edit_message_text("❌ Ошибка", call.message.chat.id, call.message.message_id)
    
    elif call.data == 'quick_unsubscribe':
        remove_subscriber(user_id)
        bot.answer_callback_query(call.id, "Отписал!")
        bot.send_message(user_id, "❌ Вы отписаны от уведомлений")

# ---------- админ: рассылка с кнопкой ----------
@bot.message_handler(commands=['admin_post'])
def admin_post(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/admin_post', '', 1).strip()
    if not text:
        bot.reply_to(message, "Используй: /admin_post текст | кнопка текст | ссылка")
        return
    
    parts = text.split('|')
    post_text = parts[0].strip()
    btn_text = parts[1].strip() if len(parts) > 1 else "Читать"
    btn_url = parts[2].strip() if len(parts) > 2 else "https://t.me"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(btn_text, url=btn_url))
    
    subscribers = get_all_subscribers()
    for user_id in subscribers:
        try:
            bot.send_message(user_id, f"📢 {post_text}", reply_markup=keyboard)
            time.sleep(0.05)
        except:
            pass
    bot.reply_to(message, f"✅ Отправлено {len(subscribers)} подписчикам")

# ---------- мониторинг ----------
def monitor_loop():
    global last_post_id
    posts = get_channel_posts(limit=1)
    if posts:
        last_post_id = posts[0]['id']
        logger.info(f"Мониторинг запущен, последний ID: {last_post_id}")
    
    while True:
        try:
            post = check_new_post()
            if post:
                logger.info(f"Новый пост! {post['link']}")
                send_to_subscribers(post['text'], post['link'], post['id'])
                bot.send_message(ADMIN_ID, f"🔔 Новый пост отправлен подписчикам!\n{post['link']}")
            
            check_inactive_users()
            time.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка мониторинга: {e}")
            time.sleep(10)

# ---------- запуск ----------
if __name__ == '__main__':
    init_db()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    logger.info(f"✅ Бот запущен! Админ: {ADMIN_ID}")
    logger.info(f"📢 Слежу за каналом: {SOURCE_CHANNEL}")
    
    bot.infinity_polling(timeout=10)