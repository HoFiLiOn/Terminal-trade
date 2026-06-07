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
BOT_NAME = "Cheats News"
API_URL = f"https://tg.i-c-a.su/json/{SOURCE_CHANNEL}"
# ============================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
last_post_data = None
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
                text = msg.get('text', '')
                if isinstance(text, list):
                    text = ' '.join(str(item) for item in text)
                if not text or text == '':
                    text = None
                
                date = datetime.fromtimestamp(msg.get('date', 0))
                msg_id = msg.get('id')
                link = f"https://t.me/{SOURCE_CHANNEL[1:]}/{msg_id}"
                
                posts.append({
                    'id': msg_id,
                    'text': text,
                    'link': link,
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

def get_channel_info():
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
                'messages_count': len(messages)
            }
            
            if messages:
                info['last_post_date'] = datetime.fromtimestamp(messages[0].get('date', 0))
            
            return info
        return None
    except Exception as e:
        logger.error(f"ошибка получения инфо: {e}")
        return None

def check_new_post():
    global last_post_data, last_check_time
    last_check_time = datetime.now()
    posts = get_channel_posts(limit=1)
    if posts:
        latest = posts[0]
        if last_post_data is None:
            last_post_data = latest
            return None
        elif latest['id'] != last_post_data['id']:
            last_post_data = latest
            return latest
    return None

# ---------- кнопки ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✅ Подписаться", callback_data='subscribe'),
        types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe')
    )
    keyboard.add(
        types.InlineKeyboardButton("📜 Последние 5", callback_data='last_5'),
        types.InlineKeyboardButton("📜 Последние 10", callback_data='last_10')
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data='stats'),
        types.InlineKeyboardButton("ℹ️ О канале", callback_data='channel_info')
    )
    keyboard.add(
        types.InlineKeyboardButton("💾 Сохранённое", callback_data='saved_posts'),
        types.InlineKeyboardButton("⚙️ Статус", callback_data='status')
    )
    keyboard.add(
        types.InlineKeyboardButton("🔧 Админ", callback_data='admin_panel')
    )
    return keyboard

def get_post_keyboard(post_link, post_text, post_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💾 Сохранить", callback_data=f'save_{post_id}'),
        types.InlineKeyboardButton("📤 Поделиться", switch_inline_query=f"{post_text[:50] if post_text else 'пост'}...")
    )
    keyboard.add(
        types.InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe'),
        types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    )
    return keyboard

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("👥 Список подписчиков", callback_data='admin_subs'),
        types.InlineKeyboardButton("📊 Полная статистика", callback_data='admin_stats'),
        types.InlineKeyboardButton("🔄 Проверить новые", callback_data='admin_check'),
        types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')
    )
    return keyboard

def get_saved_posts_keyboard(posts):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for post_id, text, link, post_date, saved_date in posts[:10]:
        keyboard.add(types.InlineKeyboardButton(f"📄 {text[:30]}...", callback_data=f'view_saved_{post_id}'))
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data='back_to_main'))
    return keyboard

# ---------- отправка постов ----------
def send_post_to_user(user_id, post):
    keyboard = get_post_keyboard(post['link'], post['text'], post['id'])
    
    if post['text']:
        text = f"<b>🔔 Новый пост в канале!</b>\n\n{post['text'][:500]}"
    else:
        text = f"<b>🔔 Новый пост в канале!</b>\n\n📷 Пост с медиафайлом"
    
    bot.send_message(
        user_id,
        text,
        reply_markup=keyboard,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

def send_first_post(user_id):
    posts = get_channel_posts(limit=1)
    if posts:
        post = posts[0]
        keyboard = get_post_keyboard(post['link'], post['text'], post['id'])
        
        if post['text']:
            text = f"<b>🎉 Добро пожаловать в Cheats News!</b>\n\nЭто последний пост в канале:\n\n{post['text'][:400]}\n\n<i>Следующие посты будут приходить автоматически</i>"
        else:
            text = f"<b>🎉 Добро пожаловать в Cheats News!</b>\n\nЭто последний пост в канале:\n\n📷 Пост с медиафайлом\n\n<i>Следующие посты будут приходить автоматически</i>"
        
        bot.send_message(
            user_id,
            text,
            reply_markup=keyboard,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        mark_first_post_sent(user_id)

def broadcast_to_subscribers(post):
    subscribers = get_all_subscribers()
    if not subscribers:
        return
    
    success = 0
    for user_id in subscribers:
        try:
            send_post_to_user(user_id, post)
            update_post_received(user_id)
            success += 1
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"ошибка {user_id}: {e}")
    
    logger.info(f"рассылка: {success}/{len(subscribers)}")
    bot.send_message(ADMIN_ID, f"📨 Пост отправлен {success}/{len(subscribers)} подписчикам")

# ---------- команды ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.send_message(
        message.chat.id,
        f"<b>👁 {BOT_NAME}</b>\n\n"
        f"Привет, <b>{user.first_name}</b>!\n\n"
        f"📢 Я слежу за каналом <b>{SOURCE_CHANNEL}</b>\n"
        f"🔔 Новости о читах приходят автоматически\n\n"
        f"👇 <b>Выбери действие:</b>",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_username"
    add_subscriber(user_id, username)
    bot.reply_to(message, f"<b>✅ Подписан!</b>\n\n👀 Подписчиков: <b>{get_subscriber_count()}</b>", parse_mode='HTML')
    
    if not was_first_post_sent(user_id):
        send_first_post(user_id)

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    user_id = message.from_user.id
    remove_subscriber(user_id)
    bot.reply_to(message, "<b>❌ Отписан</b>\n\nУведомления отключены", parse_mode='HTML')

# ---------- обработка callback'ов ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
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
            send_first_post(user_id)
    
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
    
    elif call.data == 'stats':
        received, opened = get_user_stats(user_id)
        total = get_subscriber_count()
        percent = int(opened/received*100) if received > 0 else 0
        
        bot.edit_message_text(
            f"<b>📊 Твоя статистика</b>\n\n"
            f"📨 Получено новостей: <b>{received}</b>\n"
            f"👁 Открыто: <b>{opened}</b>\n"
            f"📈 Процент открытий: <b>{percent}%</b>\n\n"
            f"👥 Всего подписчиков: <b>{total}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    elif call.data == 'status':
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        bot.edit_message_text(
            f"<b>🤖 Статус бота</b>\n\n"
            f"🟢 Статус: <b>онлайн</b>\n"
            f"📡 Api: <b>{api_status}</b>\n"
            f"👥 Подписчиков: <b>{get_subscriber_count()}</b>\n"
            f"🕐 Работает: <b>{days}д {hours}ч {minutes}м</b>\n"
            f"🔄 Последняя проверка: <b>{last_check_time.strftime('%H:%M:%S') if last_check_time else 'ещё нет'}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    elif call.data == 'channel_info':
        bot.edit_message_text(
            "<i>📊 Загружаю информацию...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        info = get_channel_info()
        if info:
            text = f"<b>📢 {info['title']}</b>\n\n"
            text += f"🔗 <b>Ссылка:</b> @{info['username']}\n"
            text += f"👥 <b>Подписчиков:</b> {info['participants_count']}\n"
            text += f"📝 <b>Постов:</b> {info['messages_count']}\n"
            if info.get('last_post_date'):
                text += f"🕐 <b>Последний пост:</b> {info['last_post_date'].strftime('%d.%m.%Y %H:%M')}\n"
            text += f"\nℹ️ <b>Описание:</b>\n{info['description'][:300]}"
            
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
                "<b>❌ Не удалось получить информацию</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    elif call.data == 'saved_posts':
        saved = get_saved_posts(user_id)
        if not saved:
            bot.edit_message_text(
                "<b>💾 У тебя пока нет сохранённых постов</b>\n\nЧтобы сохранить — нажми 💾 под постом",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                f"<b>💾 Сохранённые посты ({len(saved)})</b>\n\nВыбери пост:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_saved_posts_keyboard(saved),
                parse_mode='HTML'
            )
    
    elif call.data.startswith('view_saved_'):
        post_id = int(call.data.split('_')[2])
        saved = get_saved_posts(user_id)
        for pid, text, link, post_date, saved_date in saved:
            if pid == post_id:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("📖 Открыть пост", url=link))
                keyboard.add(types.InlineKeyboardButton("🗑 Удалить", callback_data=f'delete_saved_{pid}'))
                keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data='saved_posts'))
                
                bot.edit_message_text(
                    f"<b>💾 Сохранённый пост</b>\n\n{text}\n\n<i>Сохранён: {saved_date}</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                break
    
    elif call.data.startswith('delete_saved_'):
        post_id = int(call.data.split('_')[2])
        delete_saved_post(post_id)
        bot.answer_callback_query(call.id, "Пост удалён")
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
                "<b>💾 Нет сохранённых постов</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    elif call.data.startswith('save_'):
        post_id = call.data.split('_')[1]
        if last_post_data and str(last_post_data['id']) == post_id:
            save_post(user_id, last_post_data['text'] or "пост без текста", last_post_data['link'], last_post_data['date'].strftime('%Y-%m-%d'))
            bot.answer_callback_query(call.id, "💾 Пост сохранён!")
        else:
            bot.answer_callback_query(call.id, "❌ Не удалось сохранить")
    
    elif call.data == 'last_5':
        bot.edit_message_text(
            "<i>⏳ Загружаю последние 5 постов...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=5)
        if posts:
            text = "<b>📜 Последние 5 новостей</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> <i>{post['date'].strftime('%d.%m.%Y %H:%M')}</i>\n"
                text += f"{post['text'][:200] if post['text'] else '📷 Пост с медиа'}\n"
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
                "<b>❌ Не удалось загрузить</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    elif call.data == 'last_10':
        bot.edit_message_text(
            "<i>⏳ Загружаю последние 10 постов...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=10)
        if posts:
            text = "<b>📜 Последние 10 новостей</b>\n\n"
            for i, post in enumerate(posts, 1):
                text += f"<b>{i}.</b> <i>{post['date'].strftime('%d.%m.%Y %H:%M')}</i>\n"
                text += f"{post['text'][:150] if post['text'] else '📷 Пост с медиа'}\n"
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
                "<b>❌ Не удалось загрузить</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            f"<b>👁 {BOT_NAME}</b>\n\n👇 <b>Выбери действие:</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
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
    
    elif call.data == 'admin_subs':
        if user_id != ADMIN_ID:
            return
        subs = get_all_subscribers()
        if subs:
            if len(subs) > 50:
                file = io.BytesIO('\n'.join(map(str, subs)).encode())
                file.name = "subscribers.txt"
                bot.send_document(call.message.chat.id, file, caption=f"📄 {len(subs)} подписчиков")
                bot.edit_message_text(
                    "📄 Список отправлен файлом",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_admin_keyboard()
                )
            else:
                text = f"<b>👥 Список подписчиков ({len(subs)})</b>\n\n"
                for i, sub in enumerate(subs, 1):
                    text += f"{i}. <code>{sub}</code>\n"
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
    
    elif call.data == 'admin_stats':
        if user_id != ADMIN_ID:
            return
        subs_count = get_subscriber_count()
        uptime = datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        
        bot.edit_message_text(
            f"<b>📊 Полная статистика</b>\n\n"
            f"👥 Подписчиков: <b>{subs_count}</b>\n"
            f"📡 Api статус: <b>{api_status}</b>\n"
            f"🕐 Аптайм: <b>{days}д {hours}ч</b>\n"
            f"👑 Админ: <code>{ADMIN_ID}</code>\n"
            f"📢 Канал: <b>{SOURCE_CHANNEL}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
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
                f"✅ <b>Найден новый пост!</b>\n\n{post['text'][:100] if post['text'] else 'пост без текста'}",
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

# ---------- мониторинг ----------
def monitor_loop():
    global last_post_data
    posts = get_channel_posts(limit=1)
    if posts:
        last_post_data = posts[0]
        logger.info(f"мониторинг запущен, последний id: {last_post_data['id']}")
    
    while True:
        try:
            post = check_new_post()
            if post:
                logger.info(f"новый пост! id: {post['id']}")
                broadcast_to_subscribers(post)
            time.sleep(10)
        except Exception as e:
            logger.error(f"ошибка мониторинга: {e}")
            time.sleep(30)

# ---------- запуск ----------
if __name__ == '__main__':
    init_db()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    logger.info(f"✅ {BOT_NAME} запущен! Админ: {ADMIN_ID}")
    logger.info(f"📢 Слежу за каналом: {SOURCE_CHANNEL}")
    
    bot.infinity_polling(timeout=10)