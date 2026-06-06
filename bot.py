import sqlite3
import logging
import sys
import requests
from datetime import datetime
import telebot
from telebot import types

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
ADMIN_ID = 8388843828
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

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()
    logger.info("База данных готова")

def add_subscriber(user_id, username):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO subscribers (user_id, username, join_date) VALUES (?, ?, ?)', 
              (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
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
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM subscribers')
    count = c.fetchone()[0]
    conn.close()
    return count

# ---------- ПОЛУЧЕНИЕ ПОСТОВ ИЗ КАНАЛА ----------
last_post_id = None

def get_channel_posts(limit=10):
    """Получает последние посты из канала через tg.i-c-a.su"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
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
        return []
    except Exception as e:
        logger.error(f"Ошибка получения постов: {e}")
        return []

def check_new_post():
    """Проверяет новые посты в канале"""
    global last_post_id
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

# ---------- РАССЫЛКА ПОДПИСЧИКАМ ----------
def send_to_subscribers(post_text, post_link):
    subscribers = get_all_subscribers()
    if not subscribers:
        return
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"🔔 НОВЫЙ ПОСТ В КАНАЛЕ!\n\n{post_text[:500]}\n\n{post_link}",
                disable_web_page_preview=True
            )
            success += 1
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    logger.info(f"Рассылка: {success}/{len(subscribers)}")

# ---------- ЦВЕТНЫЕ КНОПКИ ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🟢 ПОДПИСАТЬСЯ", callback_data='subscribe')
    btn2 = types.InlineKeyboardButton("🔴 ОТПИСАТЬСЯ", callback_data='unsubscribe')
    btn3 = types.InlineKeyboardButton("🔵 ПОСЛЕДНИЕ 5", callback_data='last_5')
    btn4 = types.InlineKeyboardButton("🔵 ПОСЛЕДНИЕ 10", callback_data='last_10')
    btn5 = types.InlineKeyboardButton("🟠 СТАТИСТИКА", callback_data='stats')
    btn6 = types.InlineKeyboardButton("🔧 АДМИН ПАНЕЛЬ", callback_data='admin_panel')
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    keyboard.add(btn5)
    keyboard.add(btn6)
    return keyboard

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("👥 СПИСОК ПОДПИСЧИКОВ", callback_data='admin_subs')
    btn2 = types.InlineKeyboardButton("📊 ПОЛНАЯ СТАТИСТИКА", callback_data='admin_stats')
    btn3 = types.InlineKeyboardButton("🔄 ПРОВЕРИТЬ НОВЫЕ ПОСТЫ", callback_data='admin_check')
    btn4 = types.InlineKeyboardButton("📨 РАССЫЛКА ВСЕМ", callback_data='admin_broadcast')
    btn5 = types.InlineKeyboardButton("◀️ НАЗАД", callback_data='back')
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    return keyboard

# ---------- КОМАНДЫ ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.send_message(
        message.chat.id,
        f"<b>👁 {BOT_NAME}</b>\n\n"
        f"Привет, <b>{user.first_name}</b>!\n\n"
        f"📢 Я слежу за каналом <b>{SOURCE_CHANNEL}</b>\n"
        f"🔔 Новые посты приходят автоматически\n\n"
        f"👇 <b>ВЫБЕРИ ДЕЙСТВИЕ:</b>",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    # ПОДПИСКА
    if call.data == 'subscribe':
        username = call.from_user.username or "без_username"
        add_subscriber(user_id, username)
        bot.edit_message_text(
            f"<b>✅ ВЫ ПОДПИСАНЫ!</b>\n\n👀 Подписчиков: <b>{get_subscriber_count()}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # ОТПИСКА
    elif call.data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.edit_message_text(
            "<b>❌ ВЫ ОТПИСАНЫ</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # СТАТИСТИКА
    elif call.data == 'stats':
        bot.edit_message_text(
            f"<b>📊 СТАТИСТИКА</b>\n\n"
            f"👀 Подписчиков: <b>{get_subscriber_count()}</b>\n"
            f"📢 Канал: <b>{SOURCE_CHANNEL}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # ПОСЛЕДНИЕ 5 ПОСТОВ
    elif call.data == 'last_5':
        bot.edit_message_text("⏳ Загружаю посты...", call.message.chat.id, call.message.message_id)
        posts = get_channel_posts(limit=5)
        if posts:
            text = "<b>📜 ПОСЛЕДНИЕ 5 ПОСТОВ</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> {post['date'].strftime('%d.%m %H:%M')}\n"
                text += f"{post['text'][:200]}\n"
                text += f"<a href='{post['link']}'>🔗 Читать</a>\n\n"
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        else:
            bot.edit_message_text(
                "❌ Не удалось загрузить посты",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard()
            )
    
    # ПОСЛЕДНИЕ 10 ПОСТОВ
    elif call.data == 'last_10':
        bot.edit_message_text("⏳ Загружаю посты...", call.message.chat.id, call.message.message_id)
        posts = get_channel_posts(limit=10)
        if posts:
            text = "<b>📜 ПОСЛЕДНИЕ 10 ПОСТОВ</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> {post['date'].strftime('%d.%m %H:%M')}\n"
                text += f"{post['text'][:150]}\n"
                text += f"<a href='{post['link']}'>🔗 Читать</a>\n\n"
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        else:
            bot.edit_message_text(
                "❌ Не удалось загрузить посты",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard()
            )
    
    # АДМИН ПАНЕЛЬ
    elif call.data == 'admin_panel':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ только для админа!")
            return
        bot.edit_message_text(
            "<b>🔧 АДМИН ПАНЕЛЬ</b>\n\nВыберите действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # АДМИН: СПИСОК ПОДПИСЧИКОВ
    elif call.data == 'admin_subs':
        if user_id != ADMIN_ID:
            return
        subs = get_all_subscribers()
        if subs:
            text = "<b>👥 СПИСОК ПОДПИСЧИКОВ</b>\n\n"
            for sub in subs:
                text += f"🆔 {sub}\n"
        else:
            text = "Нет подписчиков"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # АДМИН: СТАТИСТИКА
    elif call.data == 'admin_stats':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            f"<b>📊 ПОЛНАЯ СТАТИСТИКА</b>\n\n"
            f"👥 Подписчиков: <b>{get_subscriber_count()}</b>\n"
            f"👑 Админ: <b>{ADMIN_ID}</b>\n"
            f"📢 Канал: <b>{SOURCE_CHANNEL}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # АДМИН: ПРОВЕРИТЬ НОВЫЕ ПОСТЫ
    elif call.data == 'admin_check':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "🔄 Проверяю новые посты...",
            call.message.chat.id,
            call.message.message_id
        )
        post = check_new_post()
        if post:
            bot.send_message(ADMIN_ID, f"✅ Найден новый пост!\n{post['link']}")
            bot.edit_message_text(
                f"✅ Найден новый пост!\n{post['link']}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard()
            )
        else:
            bot.edit_message_text(
                "❌ Новых постов нет",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard()
            )
    
    # АДМИН: РАССЫЛКА
    elif call.data == 'admin_broadcast':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "📨 Отправьте сообщение для рассылки всем подписчикам:",
            call.message.chat.id,
            call.message.message_id
        )
        bot.register_next_step_handler(call.message, broadcast_message)
    
    # НАЗАД
    elif call.data == 'back':
        bot.edit_message_text(
            f"<b>👁 {BOT_NAME}</b>\n\n👇 <b>ВЫБЕРИ ДЕЙСТВИЕ:</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )

# ---------- РАССЫЛКА ОТ АДМИНА ----------
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    subscribers = get_all_subscribers()
    if not subscribers:
        bot.send_message(message.chat.id, "Нет подписчиков")
        return
    
    bot.send_message(message.chat.id, f"📤 Рассылаю {len(subscribers)} подписчикам...")
    
    success = 0
    for user_id in subscribers:
        try:
            bot.forward_message(user_id, message.chat.id, message.message_id)
            success += 1
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    bot.send_message(message.chat.id, f"✅ Готово! Отправлено: {success}/{len(subscribers)}")

# ---------- МОНИТОРИНГ НОВЫХ ПОСТОВ ----------
def monitor_loop():
    """Фоновый мониторинг новых постов"""
    global last_post_id
    
    # Инициализируем last_post_id
    posts = get_channel_posts(limit=1)
    if posts:
        last_post_id = posts[0]['id']
        logger.info(f"Начат мониторинг, последний ID: {last_post_id}")
    
    while True:
        try:
            post = check_new_post()
            if post:
                logger.info(f"Новый пост! {post['link']}")
                send_to_subscribers(post['text'], post['link'])
                bot.send_message(ADMIN_ID, f"🔔 Новый пост отправлен подписчикам!\n{post['link']}")
            import time
            time.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка мониторинга: {e}")
            import time
            time.sleep(10)

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    init_db()
    
    import threading
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    logger.info(f"✅ Бот запущен! Админ: {ADMIN_ID}")
    logger.info(f"📢 Слежу за каналом: {SOURCE_CHANNEL}")
    
    bot.infinity_polling(timeout=10)