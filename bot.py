import sqlite3
import logging
import sys
import requests
import threading
import time
import io
from datetime import datetime
from telebot import TeleBot, types

# ========== конфиг ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
ADMIN_ID = 8388843828
SOURCE_CHANNEL = '@TWSA_HOF'
BOT_NAME = "Vexor Observer"
API_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}"
ITEMS_PER_PAGE = 10  # сколько подписчиков на страницу
# ============================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot = TeleBot(BOT_TOKEN)
last_post_id = None
last_post_text = None
bot_start_time = datetime.now()
last_check_time = None
api_status = "проверяется"

# ---------- база данных ----------
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT, first_post_sent INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, posts_received INTEGER DEFAULT 0, posts_opened INTEGER DEFAULT 0, last_activity TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS saved_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, post_text TEXT, post_date TEXT, saved_date TEXT)''')
    conn.commit()
    conn.close()

def add_subscriber(user_id, username, first_name, last_name):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO subscribers 
                 (user_id, username, first_name, last_name, join_date, first_post_sent) 
                 VALUES (?, ?, ?, ?, ?, 0)''', 
              (user_id, username or "нет", first_name or "нет", last_name or "нет", 
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute('''INSERT OR IGNORE INTO user_stats 
                 (user_id, posts_received, posts_opened, last_activity) 
                 VALUES (?, 0, 0, ?)''',
              (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def remove_subscriber(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_subscribers(page=1, search=None):
    """получает подписчиков с пагинацией"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE
    
    if search:
        c.execute('''SELECT user_id, username, first_name, last_name, join_date 
                     FROM subscribers 
                     WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?
                     ORDER BY join_date DESC 
                     LIMIT ? OFFSET ?''',
                  (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', ITEMS_PER_PAGE, offset))
    else:
        c.execute('''SELECT user_id, username, first_name, last_name, join_date 
                     FROM subscribers 
                     ORDER BY join_date DESC 
                     LIMIT ? OFFSET ?''', (ITEMS_PER_PAGE, offset))
    
    rows = c.fetchall()
    
    # считаем общее количество
    if search:
        c.execute('''SELECT COUNT(*) FROM subscribers 
                     WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?''',
                  (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        c.execute('SELECT COUNT(*) FROM subscribers')
    
    total = c.fetchone()[0]
    conn.close()
    return rows, total

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

def save_post(user_id, post_text, post_date):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''INSERT INTO saved_posts (user_id, post_text, post_date, saved_date) 
                 VALUES (?, ?, ?, ?)''',
              (user_id, post_text[:500], post_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_saved_posts(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''SELECT id, post_text, post_date, saved_date 
                 FROM saved_posts WHERE user_id = ? ORDER BY saved_date DESC''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_saved_post(post_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('DELETE FROM saved_posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

def get_user_info(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT username, first_name, last_name, join_date FROM subscribers WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# ---------- получение постов из канала ----------
def extract_text_from_message(msg):
    text = msg.get('text', '')
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict):
                parts.append(item.get('text', ''))
            else:
                parts.append(str(item))
        text = ' '.join(parts)
    if not text or text == '':
        return None
    return text.strip()

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
                text = extract_text_from_message(msg)
                if text is None:
                    continue
                date = datetime.fromtimestamp(msg.get('date', 0))
                msg_id = msg.get('id')
                posts.append({
                    'id': msg_id,
                    'text': text,
                    'date': date
                })
            return posts
        else:
            api_status = f"ошибка {response.status_code}"
            return []
    except Exception as e:
        api_status = "недоступен"
        logger.error(f"ошибка api: {e}")
        return []

def check_new_post():
    global last_post_id, last_check_time, last_post_text
    last_check_time = datetime.now()
    posts = get_channel_posts(limit=1)
    if posts:
        latest = posts[0]
        if last_post_id is None:
            last_post_id = latest['id']
            last_post_text = latest['text']
            return None
        elif latest['id'] != last_post_id:
            last_post_id = latest['id']
            last_post_text = latest['text']
            return latest
    return None

# ---------- цветные кнопки ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_subscribe = types.InlineKeyboardButton("✅ Подписаться", callback_data='subscribe', style='success')
    btn_unsubscribe = types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe', style='danger')
    btn_last5 = types.InlineKeyboardButton("📜 Последние 5", callback_data='last_5', style='primary')
    btn_last10 = types.InlineKeyboardButton("📜 Последние 10", callback_data='last_10', style='primary')
    btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data='stats', style='primary')
    btn_channel = types.InlineKeyboardButton("ℹ️ О канале", callback_data='channel_info', style='primary')
    btn_status = types.InlineKeyboardButton("⚙️ Статус", callback_data='status', style='primary')
    btn_saved = types.InlineKeyboardButton("💾 Сохранённое", callback_data='saved_posts', style='primary')
    btn_admin = types.InlineKeyboardButton("🔧 Админ", callback_data='admin_panel', style='danger')
    
    keyboard.add(btn_subscribe, btn_unsubscribe)
    keyboard.add(btn_last5, btn_last10)
    keyboard.add(btn_stats, btn_channel)
    keyboard.add(btn_status, btn_saved)
    keyboard.add(btn_admin)
    return keyboard

def get_post_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn_save = types.InlineKeyboardButton("💾 Сохранить пост", callback_data='save_current', style='primary')
    btn_unsub = types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe', style='danger')
    keyboard.add(btn_save, btn_unsub)
    return keyboard

def get_back_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main', style='primary')
    keyboard.add(btn_back)
    return keyboard

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn_subs = types.InlineKeyboardButton("👥 Список подписчиков", callback_data='admin_subs', style='primary')
    btn_stats = types.InlineKeyboardButton("📊 Полная статистика", callback_data='admin_stats', style='primary')
    btn_check = types.InlineKeyboardButton("🔄 Проверить новые", callback_data='admin_check', style='primary')
    btn_broadcast = types.InlineKeyboardButton("📨 Массовая рассылка", callback_data='admin_broadcast', style='primary')
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main', style='danger')
    keyboard.add(btn_subs, btn_stats, btn_check, btn_broadcast, btn_back)
    return keyboard

def get_subs_keyboard(page, total_pages, search=None):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # кнопки навигации (стрелочки)
    nav_buttons = []
    if page > 1:
        if search:
            nav_buttons.append(types.InlineKeyboardButton("◀️ Пред.", callback_data=f'subs_page_{page-1}_{search}'))
        else:
            nav_buttons.append(types.InlineKeyboardButton("◀️ Пред.", callback_data=f'subs_page_{page-1}'))
    
    nav_buttons.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data='noop', style='primary'))
    
    if page < total_pages:
        if search:
            nav_buttons.append(types.InlineKeyboardButton("След. ▶️", callback_data=f'subs_page_{page+1}_{search}'))
        else:
            nav_buttons.append(types.InlineKeyboardButton("След. ▶️", callback_data=f'subs_page_{page+1}'))
    
    keyboard.add(*nav_buttons)
    
    # кнопка поиска
    btn_search = types.InlineKeyboardButton("🔍 Поиск", callback_data='admin_search_subs', style='primary')
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='admin_panel', style='danger')
    keyboard.add(btn_search, btn_back)
    
    return keyboard

# ---------- отправка поста ----------
def send_post_to_user(user_id, post_text):
    try:
        keyboard = get_post_keyboard()
        full_text = f"🔔 Новый пост в канале {SOURCE_CHANNEL}\n\n{post_text}"
        bot.send_message(user_id, full_text, reply_markup=keyboard, disable_web_page_preview=True)
        update_post_received(user_id)
        return True
    except Exception as e:
        if "Forbidden" in str(e):
            remove_subscriber(user_id)
        logger.error(f"ошибка {user_id}: {e}")
        return False

def send_first_post_to_user(user_id, post_text):
    try:
        keyboard = get_post_keyboard()
        full_text = f"🎉 Добро пожаловать!\n\nЭто последний пост в канале {SOURCE_CHANNEL}:\n\n{post_text}\n\nСледующие посты будут приходить автоматически"
        bot.send_message(user_id, full_text, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"ошибка {user_id}: {e}")

def broadcast_to_subscribers(post_text):
    subscribers, total = get_all_subscribers(page=1)
    success = 0
    for sub in subscribers:
        user_id = sub[0]
        if send_post_to_user(user_id, post_text):
            success += 1
        time.sleep(0.05)
    logger.info(f"рассылка: {success}/{total}")

# ---------- команды ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    add_subscriber(user.id, user.username, user.first_name, user.last_name)
    bot.send_message(
        message.chat.id,
        f"👁 {BOT_NAME}\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"📢 Я слежу за каналом {SOURCE_CHANNEL}\n"
        f"🔔 Новые посты приходят автоматически\n\n"
        f"👇 Выбери действие:",
        reply_markup=get_main_keyboard()
    )
    
    if not was_first_post_sent(user.id):
        posts = get_channel_posts(limit=1)
        if posts:
            send_first_post_to_user(user.id, posts[0]['text'])
            mark_first_post_sent(user.id)

@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    user = message.from_user
    add_subscriber(user.id, user.username, user.first_name, user.last_name)
    bot.reply_to(message, f"✅ Подписан!\n\n👀 Подписчиков: {get_subscriber_count()}")
    
    if not was_first_post_sent(user.id):
        posts = get_channel_posts(limit=1)
        if posts:
            send_first_post_to_user(user.id, posts[0]['text'])
            mark_first_post_sent(user.id)

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    remove_subscriber(message.from_user.id)
    bot.reply_to(message, "❌ Отписан\n\nУведомления отключены")

# ---------- callback обработчик ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    # подписка
    if data == 'subscribe':
        user = call.from_user
        add_subscriber(user.id, user.username, user.first_name, user.last_name)
        bot.answer_callback_query(call.id, "Подписал!")
        bot.edit_message_text(
            f"✅ Подписан!\n\n👀 Подписчиков: {get_subscriber_count()}\n\n👇 Выбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
        if not was_first_post_sent(user.id):
            posts = get_channel_posts(limit=1)
            if posts:
                send_first_post_to_user(user.id, posts[0]['text'])
                mark_first_post_sent(user.id)
    
    # отписка
    elif data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.answer_callback_query(call.id, "Отписал!")
        bot.edit_message_text(
            "❌ Отписан\n\nУведомления отключены",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    # сохранение текущего поста
    elif data == 'save_current':
        global last_post_text
        if last_post_text:
            save_post(user_id, last_post_text, datetime.now().strftime('%Y-%m-%d'))
            bot.answer_callback_query(call.id, "💾 Пост сохранён!")
        else:
            bot.answer_callback_query(call.id, "❌ Нет поста для сохранения")
    
    # сохранённые посты
    elif data == 'saved_posts':
        saved = get_saved_posts(user_id)
        if not saved:
            bot.edit_message_text(
                "💾 У тебя пока нет сохранённых постов\n\nЧтобы сохранить пост — нажми 💾 под любым постом",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        else:
            text = f"💾 Твои сохранённые посты ({len(saved)})\n\n"
            for i, (pid, post_text, post_date, saved_date) in enumerate(saved[:5], 1):
                text += f"{i}. {post_text[:80]}...\n📅 {saved_date}\n\n"
            if len(saved) > 5:
                text += f"и ещё {len(saved)-5} постов"
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard(),
                disable_web_page_preview=True
            )
    
    # статистика пользователя
    elif data == 'stats':
        received, opened = get_user_stats(user_id)
        total = get_subscriber_count()
        percent = int(opened/received*100) if received > 0 else 0
        text = f"📊 Твоя статистика\n\n📨 Получено постов: {received}\n👁 Открыто постов: {opened}\n📈 Процент открытий: {percent}%\n\n👥 Всего подписчиков: {total}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    
    # статус бота
    elif data == 'status':
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        text = f"🤖 Статус бота\n\n🟢 Статус: онлайн\n📡 Api: {api_status}\n👥 Подписчиков: {get_subscriber_count()}\n🕐 Работает: {days}д {hours}ч {minutes}м\n🔄 Последняя проверка: {last_check_time.strftime('%H:%M:%S') if last_check_time else 'ещё нет'}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    
    # информация о канале
    elif data == 'channel_info':
        text = f"📢 Информация о канале\n\n🔗 Название: {SOURCE_CHANNEL}\n📢 Бот следит за этим каналом\n🔔 Новые посты приходят автоматически"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    
    # последние посты
    elif data in ['last_5', 'last_10']:
        limit = 5 if data == 'last_5' else 10
        bot.edit_message_text("⏳ Загружаю...", call.message.chat.id, call.message.message_id)
        posts = get_channel_posts(limit=limit)
        if posts:
            text = f"📜 Последние {limit} постов\n\n"
            for i, post in enumerate(posts, 1):
                text += f"{i}. {post['date'].strftime('%d.%m.%Y %H:%M')}\n{post['text'][:150]}\n\n"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard(), disable_web_page_preview=True)
        else:
            bot.edit_message_text("❌ Не удалось загрузить посты", call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())
    
    # назад в главное меню
    elif data == 'back_to_main':
        bot.edit_message_text(
            f"👁 {BOT_NAME}\n\n👇 Выбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    # админ панель
    elif data == 'admin_panel':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ только для админа!")
            return
        bot.edit_message_text(
            "🔧 Админ панель\n\nВыбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard()
        )
    
    # админ: список подписчиков с пагинацией
    elif data.startswith('admin_subs'):
        bot.edit_message_text(
            "👥 Загружаю список подписчиков...",
            call.message.chat.id,
            call.message.message_id
        )
        show_subscribers_page(call.message.chat.id, call.message.message_id, page=1)
    
    # пагинация подписчиков
    elif data.startswith('subs_page_'):
        parts = data.split('_')
        page = int(parts[2])
        search = '_'.join(parts[3:]) if len(parts) > 3 else None
        show_subscribers_page(call.message.chat.id, call.message.message_id, page, search)
    
    # поиск подписчиков
    elif data == 'admin_search_subs':
        msg = bot.send_message(call.message.chat.id, "🔍 Введи имя, юзернейм или ID для поиска:")
        bot.register_next_step_handler(msg, search_subscribers, call.message.chat.id, call.message.message_id)
    
    # админ: полная статистика
    elif data == 'admin_stats':
        if user_id != ADMIN_ID:
            return
        subs_count = get_subscriber_count()
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        text = f"📊 Полная статистика\n\n👥 Подписчиков: {subs_count}\n📡 Api статус: {api_status}\n🕐 Аптайм: {days}д {hours}ч\n👑 Админ: {ADMIN_ID}\n📢 Канал: {SOURCE_CHANNEL}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_admin_keyboard())
    
    # админ: проверить новые посты
    elif data == 'admin_check':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text("🔄 Проверяю...", call.message.chat.id, call.message.message_id)
        post = check_new_post()
        if post:
            bot.edit_message_text(f"✅ Найден новый пост!\n\n{post['text'][:200]}", call.message.chat.id, call.message.message_id, reply_markup=get_admin_keyboard())
            broadcast_to_subscribers(post['text'])
            bot.send_message(ADMIN_ID, f"🔔 Новый пост отправлен подписчикам!")
        else:
            bot.edit_message_text("❌ Новых постов нет", call.message.chat.id, call.message.message_id, reply_markup=get_admin_keyboard())
    
    # админ: массовая рассылка
    elif data == 'admin_broadcast':
        if user_id != ADMIN_ID:
            return
        msg = bot.send_message(call.message.chat.id, "📨 Введи текст для массовой рассылки:")
        bot.register_next_step_handler(msg, broadcast_message, call.message.chat.id, call.message.message_id)
    
    # пустая кнопка
    elif data == 'noop':
        bot.answer_callback_query(call.id)

def show_subscribers_page(chat_id, message_id, page=1, search=None):
    """показывает страницу со списком подписчиков"""
    subscribers, total = get_all_subscribers(page=page, search=search)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if not subscribers:
        text = "👥 Нет подписчиков"
        if search:
            text = f"🔍 По запросу '{search}' ничего не найдено"
        bot.edit_message_text(text, chat_id, message_id, reply_markup=get_admin_keyboard())
        return
    
    text = f"👥 Список подписчиков (всего: {total})\n\n"
    for sub in subscribers:
        user_id, username, first_name, last_name, join_date = sub
        name = first_name if first_name != "нет" else username if username != "нет" else str(user_id)
        text += f"👤 {name}\n🆔 {user_id}\n📅 {join_date}\n\n"
    
    # если текста много, отправляем файлом
    if len(text) > 3500:
        file = io.BytesIO(text.encode('utf-8'))
        file.name = "subscribers.txt"
        bot.send_document(chat_id, file, caption=f"📄 {total} подписчиков (страница {page}/{total_pages})")
        bot.edit_message_text(
            f"📄 Список отправлен файлом (страница {page}/{total_pages})",
            chat_id,
            message_id,
            reply_markup=get_subs_keyboard(page, total_pages, search)
        )
    else:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=get_subs_keyboard(page, total_pages, search)
        )

def search_subscribers(message, original_chat_id, original_message_id):
    """поиск подписчиков"""
    search_query = message.text.strip()
    if not search_query:
        bot.send_message(message.chat.id, "❌ Поиск отменён")
        return
    
    subscribers, total = get_all_subscribers(page=1, search=search_query)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if not subscribers:
        bot.send_message(message.chat.id, f"🔍 По запросу '{search_query}' ничего не найдено")
        show_subscribers_page(original_chat_id, original_message_id, page=1)
        return
    
    text = f"🔍 Результаты поиска: '{search_query}' (найдено: {total})\n\n"
    for sub in subscribers:
        user_id, username, first_name, last_name, join_date = sub
        name = first_name if first_name != "нет" else username if username != "нет" else str(user_id)
        text += f"👤 {name}\n🆔 {user_id}\n📅 {join_date}\n\n"
    
    bot.send_message(message.chat.id, text[:4000])
    show_subscribers_page(original_chat_id, original_message_id, page=1, search=search_query)

def broadcast_message(message, original_chat_id, original_message_id):
    """отправляет массовую рассылку"""
    if message.from_user.id != ADMIN_ID:
        return
    
    broadcast_text = message.text.strip()
    if not broadcast_text:
        bot.send_message(message.chat.id, "❌ Рассылка отменена")
        return
    
    subscribers, total = get_all_subscribers(page=1)
    bot.send_message(message.chat.id, f"📨 Начинаю рассылку {total} подписчикам...")
    
    success = 0
    for sub in subscribers:
        user_id = sub[0]
        try:
            bot.send_message(user_id, f"📢 Массовое сообщение\n\n{broadcast_text}")
            success += 1
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"ошибка {user_id}: {e}")
    
    bot.send_message(message.chat.id, f"✅ Рассылка завершена! Отправлено: {success}/{total}")
    show_subscribers_page(original_chat_id, original_message_id, page=1)

# ---------- мониторинг ----------
def monitor_loop():
    global last_post_id
    posts = get_channel_posts(limit=1)
    if posts:
        last_post_id = posts[0]['id']
        logger.info(f"мониторинг запущен, последний id: {last_post_id}")
    
    while True:
        try:
            post = check_new_post()
            if post:
                logger.info(f"новый пост!")
                broadcast_to_subscribers(post['text'])
                bot.send_message(ADMIN_ID, f"🔔 Новый пост отправлен подписчикам!\n\n{post['text'][:200]}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"ошибка мониторинга: {e}")
            time.sleep(10)

# ---------- запуск ----------
if __name__ == '__main__':
    init_db()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    logger.info(f"✅ бот запущен! админ: {ADMIN_ID}")
    logger.info(f"📢 слежу за каналом: {SOURCE_CHANNEL}")
    
    bot.infinity_polling(timeout=10)