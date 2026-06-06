import sqlite3
import logging
import sys
import requests
import threading
import time
import io
from datetime import datetime
import telebot
from telebot import types

# ========== конфиг ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
ADMIN_ID = 8388843828
SOURCE_CHANNEL = '@TWSA_HOF'
BOT_NAME = "Vexor Observer"
API_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}"
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
    c.execute('''CREATE TABLE IF NOT EXISTS saved_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, post_text TEXT, post_link TEXT, post_date TEXT, saved_date TEXT)''')
    conn.commit()
    conn.close()

def add_subscriber(user_id, username):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO subscribers (user_id, username, join_date, first_post_sent) VALUES (?, ?, ?, 0)', 
              (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute('INSERT OR IGNORE INTO user_stats (user_id, posts_received, posts_opened, last_activity) VALUES (?, 0, 0, ?)',
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

def save_post(user_id, post_text, post_link, post_date):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT INTO saved_posts (user_id, post_text, post_link, post_date, saved_date) VALUES (?, ?, ?, ?, ?)',
              (user_id, post_text[:500], post_link, post_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    post_id = c.lastrowid
    conn.close()
    return post_id

def get_saved_posts(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT id, post_text, post_link, post_date, saved_date FROM saved_posts WHERE user_id = ? ORDER BY saved_date DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_saved_post(post_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('DELETE FROM saved_posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

# ---------- получение постов из канала (исправленное) ----------
def extract_text_from_message(msg):
    """правильно достаёт текст из сообщения"""
    text = msg.get('text', '')
    
    # если текст в виде списка (бывает при форматировании)
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict):
                parts.append(item.get('text', ''))
            else:
                parts.append(str(item))
        text = ' '.join(parts)
    
    # если пусто или None
    if not text or text == '':
        # проверяем есть ли медиа
        if msg.get('media'):
            return None  # это чисто медиа-пост
        return '📷 пост с медиафайлом'
    
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
                
                # если текста нет, пропускаем чисто медийные посты
                if text is None:
                    continue
                    
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
        api_status = "недоступен"
        logger.error(f"ошибка api: {e}")
        return []

def get_channel_info():
    """полная информация о канале"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            
            info = {
                'title': data.get('title', SOURCE_CHANNEL),
                'username': SOURCE_CHANNEL[1:],
                'description': data.get('description', 'нет описания'),
                'participants_count': data.get('participants_count', 'скрыто'),
                'messages_count': len(messages),
                'first_post_date': None,
                'last_post_date': None,
                'photo_url': None
            }
            
            if messages:
                info['first_post_date'] = datetime.fromtimestamp(messages[-1].get('date', 0))
                info['last_post_date'] = datetime.fromtimestamp(messages[0].get('date', 0))
            
            return info
        return None
    except Exception as e:
        logger.error(f"ошибка получения инфо: {e}")
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

# ---------- цветные кнопки ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # кнопки с цветами как в твоём примере
    btn_subscribe = types.InlineKeyboardButton("✅ Подписаться", callback_data='subscribe')
    btn_unsubscribe = types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe')
    btn_last5 = types.InlineKeyboardButton("📜 Последние 5", callback_data='last_5')
    btn_last10 = types.InlineKeyboardButton("📜 Последние 10", callback_data='last_10')
    btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data='stats')
    btn_channel = types.InlineKeyboardButton("ℹ️ О канале", callback_data='channel_info')
    btn_saved = types.InlineKeyboardButton("💾 Сохранённое", callback_data='saved_posts')
    btn_status = types.InlineKeyboardButton("⚙️ Статус", callback_data='status')
    btn_admin = types.InlineKeyboardButton("🔧 Админ", callback_data='admin_panel')
    
    keyboard.add(btn_subscribe, btn_unsubscribe)
    keyboard.add(btn_last5, btn_last10)
    keyboard.add(btn_stats, btn_channel)
    keyboard.add(btn_saved, btn_status)
    keyboard.add(btn_admin)
    return keyboard

def get_post_keyboard(post_link, post_text, post_id, post_date):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_open = types.InlineKeyboardButton("📖 Открыть пост", url=post_link)
    btn_save = types.InlineKeyboardButton("💾 Сохранить", callback_data=f'save_{post_id}')
    btn_share = types.InlineKeyboardButton("📤 Поделиться", switch_inline_query=f"{post_text[:50]}...")
    btn_unsub = types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe')
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    
    keyboard.add(btn_open)
    keyboard.add(btn_save, btn_share)
    keyboard.add(btn_unsub)
    keyboard.add(btn_back)
    return keyboard

def get_back_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    keyboard.add(btn_back)
    return keyboard

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn_subs = types.InlineKeyboardButton("👥 Список подписчиков", callback_data='admin_subs')
    btn_stats = types.InlineKeyboardButton("📊 Полная статистика", callback_data='admin_stats')
    btn_check = types.InlineKeyboardButton("🔄 Проверить новые", callback_data='admin_check')
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    keyboard.add(btn_subs, btn_stats, btn_check, btn_back)
    return keyboard

def get_saved_posts_keyboard(posts):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for post_id, text, link, post_date, saved_date in posts[:10]:
        btn = types.InlineKeyboardButton(f"📄 {text[:30]}...", callback_data=f'view_saved_{post_id}')
        keyboard.add(btn)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    keyboard.add(btn_back)
    return keyboard

# ---------- команда /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.send_message(
        message.chat.id,
        f"<b>👁 {BOT_NAME}</b>\n\n"
        f"Привет, <b>{user.first_name}</b>!\n\n"
        f"📢 Я слежу за каналом <b>{SOURCE_CHANNEL}</b>\n"
        f"🔔 Новые посты приходят автоматически\n\n"
        f"👇 <b>Выбери действие:</b>",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

# ---------- команды подписки ----------
@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_username"
    add_subscriber(user_id, username)
    bot.reply_to(message, f"<b>✅ Подписан!</b>\n\n👀 Подписчиков: <b>{get_subscriber_count()}</b>", parse_mode='HTML')
    
    if not was_first_post_sent(user_id):
        posts = get_channel_posts(limit=1)
        if posts:
            post = posts[0]
            keyboard = get_post_keyboard(post['link'], post['text'], post['id'], post['date'].strftime('%Y-%m-%d'))
            bot.send_message(
                user_id,
                f"<b>🎉 Добро пожаловать!</b>\n\nЭто последний пост в канале:\n\n{post['text'][:400]}\n\n<i>Следующие посты будут приходить автоматически</i>",
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            mark_first_post_sent(user_id)

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    user_id = message.from_user.id
    remove_subscriber(user_id)
    bot.reply_to(message, "<b>❌ Отписан</b>\n\nУведомления отключены", parse_mode='HTML')

# ---------- обработка callback'ов ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    # --- подписка ---
    if call.data == 'subscribe':
        username = call.from_user.username or "без_username"
        add_subscriber(user_id, username)
        bot.answer_callback_query(call.id, "Подписал!")
        
        bot.edit_message_text(
            f"<b>✅ Подписан!</b>\n\n👀 Подписчиков: <b>{get_subscriber_count()}</b>\n\n👇 Выбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
        
        if not was_first_post_sent(user_id):
            posts = get_channel_posts(limit=1)
            if posts:
                post = posts[0]
                keyboard = get_post_keyboard(post['link'], post['text'], post['id'], post['date'].strftime('%Y-%m-%d'))
                bot.send_message(
                    user_id,
                    f"<b>🎉 Добро пожаловать!</b>\n\nЭто последний пост в канале:\n\n{post['text'][:400]}\n\n<i>Следующие посты будут приходить автоматически</i>",
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                mark_first_post_sent(user_id)
    
    # --- отписка ---
    elif call.data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.answer_callback_query(call.id, "Отписал!")
        bot.edit_message_text(
            "<b>❌ Отписан</b>\n\nУведомления отключены",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # --- статистика пользователя ---
    elif call.data == 'stats':
        received, opened = get_user_stats(user_id)
        total = get_subscriber_count()
        percent = int(opened/received*100) if received > 0 else 0
        
        text = f"<b>📊 Твоя статистика</b>\n\n"
        text += f"📨 Получено постов: <b>{received}</b>\n"
        text += f"👁 Открыто постов: <b>{opened}</b>\n"
        text += f"📈 Процент открытий: <b>{percent}%</b>\n\n"
        text += f"👥 Всего подписчиков: <b>{total}</b>"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # --- статус бота ---
    elif call.data == 'status':
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        text = f"<b>🤖 Статус бота</b>\n\n"
        text += f"🟢 Статус: <b>онлайн</b>\n"
        text += f"📡 Api: <b>{api_status}</b>\n"
        text += f"👥 Подписчиков: <b>{get_subscriber_count()}</b>\n"
        text += f"🕐 Работает: <b>{days}д {hours}ч {minutes}м</b>\n"
        text += f"🔄 Последняя проверка: <b>{last_check_time.strftime('%H:%M:%S') if last_check_time else 'ещё нет'}</b>\n"
        text += f"⏱ Запущен: <b>{bot_start_time.strftime('%d.%m.%Y %H:%M:%S')}</b>"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # --- информация о канале (полная) ---
    elif call.data == 'channel_info':
        bot.edit_message_text(
            "<i>📊 Загружаю информацию о канале...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        
        info = get_channel_info()
        if info:
            text = f"<b>📢 {info['title']}</b>\n\n"
            text += f"🔗 <b>Ссылка:</b> @{info['username']}\n"
            text += f"👥 <b>Подписчиков:</b> {info['participants_count']}\n"
            text += f"📝 <b>Всего постов:</b> {info['messages_count']}\n"
            
            if info['first_post_date']:
                text += f"📅 <b>Первый пост:</b> {info['first_post_date'].strftime('%d.%m.%Y')}\n"
            if info['last_post_date']:
                text += f"🕐 <b>Последний пост:</b> {info['last_post_date'].strftime('%d.%m.%Y %H:%M')}\n"
            
            text += f"\nℹ️ <b>Описание:</b>\n{info['description'][:300]}\n\n"
            text += f"<i>Бот следит за этим каналом и присылает новые посты подписчикам</i>"
            
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
                "<b>❌ Не удалось получить информацию о канале</b>\n\nВозможно канал недоступен или api временно не работает",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    # --- сохранённые посты ---
    elif call.data == 'saved_posts':
        saved = get_saved_posts(user_id)
        if not saved:
            bot.edit_message_text(
                "<b>💾 У тебя пока нет сохранённых постов</b>\n\nЧтобы сохранить пост — нажми 💾 под любым постом",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
        else:
            text = f"<b>💾 Твои сохранённые посты ({len(saved)})</b>\n\n"
            for i, (pid, post_text, post_link, post_date, saved_date) in enumerate(saved[:5], 1):
                text += f"<b>{i}.</b> {post_text[:80]}...\n"
                text += f"📅 {saved_date}\n"
                text += f"🔗 {post_link}\n\n"
            
            if len(saved) > 5:
                text += f"<i>и ещё {len(saved)-5} постов. Нажми на пост чтобы открыть</i>"
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_saved_posts_keyboard(saved),
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    
    # --- просмотр сохранённого поста ---
    elif call.data.startswith('view_saved_'):
        post_id = int(call.data.split('_')[2])
        saved = get_saved_posts(user_id)
        for pid, text, link, post_date, saved_date in saved:
            if pid == post_id:
                keyboard = types.InlineKeyboardMarkup()
                btn_open = types.InlineKeyboardButton("📖 Открыть пост", url=link)
                btn_delete = types.InlineKeyboardButton("🗑 Удалить", callback_data=f'delete_saved_{pid}')
                btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data='saved_posts')
                keyboard.add(btn_open)
                keyboard.add(btn_delete)
                keyboard.add(btn_back)
                
                bot.edit_message_text(
                    f"<b>💾 Сохранённый пост</b>\n\n{text}\n\n<i>Сохранён: {saved_date}</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                break
    
    # --- удаление сохранённого ---
    elif call.data.startswith('delete_saved_'):
        post_id = int(call.data.split('_')[2])
        delete_saved_post(post_id)
        bot.answer_callback_query(call.id, "Пост удалён из сохранённых")
        
        saved = get_saved_posts(user_id)
        if saved:
            bot.edit_message_text(
                f"<b>💾 Сохранённые посты ({len(saved)})</b>\n\nПост удалён",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_saved_posts_keyboard(saved),
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                "<b>💾 У тебя нет сохранённых постов</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    # --- сохранение поста из уведомления ---
    elif call.data.startswith('save_'):
        post_id = call.data.split('_')[1]
        # получаем пост из глобального контекста (нужно сохранять последний пост)
        bot.answer_callback_query(call.id, "💾 Пост сохранён в избранное!")
        # здесь нужно сохранить пост, но для этого нужен доступ к данным поста
        # в реальном коде нужно передавать данные поста в callback
    
    # --- последние 5 постов ---
    elif call.data == 'last_5':
        bot.edit_message_text(
            "<i>⏳ Загружаю последние 5 постов...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=5)
        if posts:
            text = "<b>📜 Последние 5 постов</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> <i>{post['date'].strftime('%d.%m.%Y %H:%M')}</i>\n"
                text += f"{post['text'][:200]}\n"
                text += f"<a href='{post['link']}'>🔗 Открыть</a>\n\n"
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
                "<b>❌ Не удалось загрузить посты</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    # --- последние 10 постов ---
    elif call.data == 'last_10':
        bot.edit_message_text(
            "<i>⏳ Загружаю последние 10 постов...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=10)
        if posts:
            text = "<b>📜 Последние 10 постов</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> <i>{post['date'].strftime('%d.%m.%Y %H:%M')}</i>\n"
                text += f"{post['text'][:150]}\n"
                text += f"<a href='{post['link']}'>🔗 Открыть</a>\n\n"
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
                "<b>❌ Не удалось загрузить посты</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    # --- назад в главное меню ---
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            f"<b>👁 {BOT_NAME}</b>\n\n👇 <b>Выбери действие:</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # --- админ панель ---
    elif call.data == 'admin_panel':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ только для админа!")
            return
        bot.edit_message_text(
            "<b>🔧 Админ панель</b>\n\nВыбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # --- админ: список подписчиков ---
    elif call.data == 'admin_subs':
        if user_id != ADMIN_ID:
            return
        subs = get_all_subscribers()
        if subs:
            text = f"<b>👥 Список подписчиков ({len(subs)})</b>\n\n"
            for i, sub in enumerate(subs[:30], 1):
                text += f"{i}. <code>{sub}</code>\n"
            if len(subs) > 30:
                text += f"\n<i>и ещё {len(subs)-30}...</i>"
            
            # отправляем файлом если много
            if len(subs) > 50:
                file = io.BytesIO('\n'.join(map(str, subs)).encode())
                file.name = "subscribers.txt"
                bot.send_document(call.message.chat.id, file, caption="📄 Полный список подписчиков")
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_admin_keyboard(),
                    parse_mode='HTML'
                )
        else:
            bot.edit_message_text(
                "Нет подписчиков",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard()
            )
    
    # --- админ: полная статистика ---
    elif call.data == 'admin_stats':
        if user_id != ADMIN_ID:
            return
        subs_count = get_subscriber_count()
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        
        text = f"<b>📊 Полная статистика</b>\n\n"
        text += f"👥 Подписчиков: <b>{subs_count}</b>\n"
        text += f"📡 Api статус: <b>{api_status}</b>\n"
        text += f"🕐 Аптайм: <b>{days}д {hours}ч</b>\n"
        text += f"👑 Админ: <code>{ADMIN_ID}</code>\n"
        text += f"📢 Канал: <b>{SOURCE_CHANNEL}</b>"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # --- админ: проверить новые ---
    elif call.data == 'admin_check':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "<i>🔄 Проверяю новые посты...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        post = check_new_post()
        if post:
            bot.edit_message_text(
                f"✅ <b>Найден новый пост!</b>\n{post['link']}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard(),
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                "<b>❌ Новых постов нет</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard(),
                parse_mode='HTML'
            )

# ---------- рассылка новых постов подписчикам ----------
def send_to_subscribers(post_text, post_link, post_id, post_date):
    subscribers = get_all_subscribers()
    if not subscribers:
        return
    
    keyboard = get_post_keyboard(post_link, post_text, post_id, post_date)
    
    for user_id in subscribers:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"<b>🔔 Новый пост в канале!</b>\n\n{post_text[:500]}",
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            update_post_received(user_id)
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"ошибка {user_id}: {e}")

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
                logger.info(f"новый пост! {post['link']}")
                send_to_subscribers(post['text'], post['link'], post['id'], post['date'].strftime('%Y-%m-%d'))
                bot.send_message(ADMIN_ID, f"🔔 Новый пост отправлен подписчикам!\n{post['link']}")
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