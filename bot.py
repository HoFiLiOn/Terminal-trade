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
    c.execute('''CREATE TABLE IF NOT EXISTS saved_posts (user_id INTEGER, post_text TEXT, post_link TEXT, saved_date TEXT)''')
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

def save_post_for_user(user_id, post_text, post_link):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('INSERT INTO saved_posts (user_id, post_text, post_link, saved_date) VALUES (?, ?, ?, ?)',
              (user_id, post_text[:500], post_link, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_saved_posts(user_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('SELECT post_text, post_link, saved_date FROM saved_posts WHERE user_id = ? ORDER BY saved_date DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

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
                text = msg.get('text', '📷 Медиафайл (нет текста)')
                if isinstance(text, list):
                    text = ' '.join(str(item) for item in text)
                if not text or text == '':
                    text = '📷 Пост с медиафайлом'
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

# ---------- главная клавиатура с html и кнопкой назад ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🟢 ПОДПИСАТЬСЯ", callback_data='subscribe')
    btn2 = types.InlineKeyboardButton("🔴 ОТПИСАТЬСЯ", callback_data='unsubscribe')
    btn3 = types.InlineKeyboardButton("🔵 ПОСЛЕДНИЕ 5", callback_data='last_5')
    btn4 = types.InlineKeyboardButton("🔵 ПОСЛЕДНИЕ 10", callback_data='last_10')
    btn5 = types.InlineKeyboardButton("🟠 СТАТИСТИКА", callback_data='stats')
    btn6 = types.InlineKeyboardButton("📊 О КАНАЛЕ", callback_data='channel_info')
    btn7 = types.InlineKeyboardButton("💾 СОХРАНЕННОЕ", callback_data='saved_posts')
    btn8 = types.InlineKeyboardButton("⚙️ СТАТУС", callback_data='status')
    btn9 = types.InlineKeyboardButton("🔧 АДМИН", callback_data='admin_panel')
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    keyboard.add(btn5, btn6)
    keyboard.add(btn7, btn8)
    keyboard.add(btn9)
    return keyboard

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("👥 СПИСОК ПОДПИСЧИКОВ", callback_data='admin_subs')
    btn2 = types.InlineKeyboardButton("📊 ПОЛНАЯ СТАТИСТИКА", callback_data='admin_stats')
    btn3 = types.InlineKeyboardButton("📨 РАССЫЛКА ВСЕМ", callback_data='admin_broadcast')
    btn4 = types.InlineKeyboardButton("📤 РАССЫЛКА С КНОПКОЙ", callback_data='admin_post_with_btn')
    btn5 = types.InlineKeyboardButton("🔄 ПРОВЕРИТЬ НОВЫЕ", callback_data='admin_check')
    btn6 = types.InlineKeyboardButton("◀️ НАЗАД", callback_data='back_to_main')
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return keyboard

def get_post_keyboard(post_link, post_text, post_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📖 ОТКРЫТЬ ПОСТ", url=post_link)
    btn2 = types.InlineKeyboardButton("💾 СОХРАНИТЬ", callback_data=f'save_{post_id}')
    btn3 = types.InlineKeyboardButton("📤 ПОДЕЛИТЬСЯ", callback_data=f'share_{post_id}')
    btn4 = types.InlineKeyboardButton("❌ ОТПИСАТЬСЯ", callback_data='unsubscribe')
    btn5 = types.InlineKeyboardButton("◀️ НАЗАД", callback_data='back_to_main')
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    keyboard.add(btn5)
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
    
    # Отправляем первый пост сразу без дубляжа
    posts = get_channel_posts(limit=1)
    if posts and not was_first_post_sent(user_id):
        post = posts[0]
        keyboard = get_post_keyboard(post['link'], post['text'], post['id'])
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
    
    # Подписка
    if call.data == 'subscribe':
        username = call.from_user.username or "без_username"
        add_subscriber(user_id, username)
        bot.answer_callback_query(call.id, "✅ Подписал!")
        
        # Показываем главное меню с уведомлением
        bot.edit_message_text(
            f"<b>✅ Подписан!</b>\n\n👀 Подписчиков: <b>{get_subscriber_count()}</b>\n\n👇 Выбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
        
        # Отправляем первый пост если еще не отправляли
        if not was_first_post_sent(user_id):
            posts = get_channel_posts(limit=1)
            if posts:
                post = posts[0]
                keyboard = get_post_keyboard(post['link'], post['text'], post['id'])
                bot.send_message(
                    user_id,
                    f"<b>🎉 Добро пожаловать!</b>\n\nЭто последний пост в канале:\n\n{post['text'][:400]}\n\n<i>Следующие посты будут приходить автоматически</i>",
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                mark_first_post_sent(user_id)
    
    # Отписка
    elif call.data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.answer_callback_query(call.id, "❌ Отписал!")
        bot.edit_message_text(
            "<b>❌ Отписан</b>\n\nУведомления отключены",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # Статистика пользователя
    elif call.data == 'stats':
        received, opened = get_user_stats(user_id)
        subscribed = get_subscriber_count()
        bot.edit_message_text(
            f"<b>📊 Твоя статистика</b>\n\n"
            f"📨 Получено постов: <b>{received}</b>\n"
            f"👁 Открыто постов: <b>{opened}</b>\n"
            f"📈 Процент открытий: <b>{int(opened/received*100) if received > 0 else 0}%</b>\n\n"
            f"👥 Всего подписчиков: <b>{subscribed}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # Статус бота
    elif call.data == 'status':
        uptime = datetime.now() - bot_start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        days = uptime.days
        
        text = f"<b>🤖 Статус бота</b>\n\n"
        text += f"🟢 Статус: <b>онлайн</b>\n"
        text += f"📡 API ({SOURCE_CHANNEL}): <b>{api_status}</b>\n"
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
    
    # Информация о канале с аватаркой
    elif call.data == 'channel_info':
        bot.edit_message_text(
            "📊 <b>Загружаю информацию о канале...</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        
        info = get_channel_info()
        if info:
            text = f"<b>📢 {info['title']}</b>\n\n"
            text += f"🔗 <b>Ссылка:</b> @{info['username']}\n"
            text += f"👥 <b>Подписчиков:</b> {info['participants_count']}\n"
            text += f"📝 <b>Постов в выборке:</b> {info['messages_count']}\n"
            text += f"ℹ️ <b>Описание:</b>\n{info['description'][:300]}\n\n"
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
                "<b>❌ Не удалось получить информацию о канале</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    # Сохраненные посты
    elif call.data == 'saved_posts':
        saved = get_saved_posts(user_id)
        if not saved:
            bot.edit_message_text(
                "<b>💾 У тебя пока нет сохраненных постов</b>\n\nЧтобы сохранить пост - нажми 💾 под любым постом",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
        else:
            text = "<b>💾 Твои сохраненные посты</b>\n\n"
            for i, (post_text, post_link, saved_date) in enumerate(saved[:5], 1):
                text += f"{i}. {post_text[:80]}...\n"
                text += f"📅 {saved_date}\n"
                text += f"🔗 {post_link}\n\n"
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard(),
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    
    # Сохранение поста
    elif call.data.startswith('save_'):
        post_id = call.data.split('_')[1]
        # Нужно получить текст поста из временного хранилища
        bot.answer_callback_query(call.id, "💾 Пост сохранен в избранное!")
    
    # Шеар
    elif call.data.startswith('share_'):
        bot.answer_callback_query(call.id, "📤 Нажми на пост и скопируй ссылку")
    
    # Последние 5 постов
    elif call.data == 'last_5':
        bot.edit_message_text(
            "⏳ <b>Загружаю последние 5 постов...</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=5)
        if posts:
            text = "<b>📜 ПОСЛЕДНИЕ 5 ПОСТОВ</b>\n\n"
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
    
    # Последние 10 постов
    elif call.data == 'last_10':
        bot.edit_message_text(
            "⏳ <b>Загружаю последние 10 постов...</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        posts = get_channel_posts(limit=10)
        if posts:
            text = "<b>📜 ПОСЛЕДНИЕ 10 ПОСТОВ</b>\n\n"
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
    
    # Назад в главное меню
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            f"<b>👁 {BOT_NAME}</b>\n\n👇 <b>Выбери действие:</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ панель
    elif call.data == 'admin_panel':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Доступ только для админа!")
            return
        bot.edit_message_text(
            "<b>🔧 АДМИН ПАНЕЛЬ</b>\n\nВыбери действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ: список подписчиков
    elif call.data == 'admin_subs':
        if user_id != ADMIN_ID:
            return
        subs = get_all_subscribers()
        if subs:
            text = "<b>👥 СПИСОК ПОДПИСЧИКОВ</b>\n\n"
            for sub in subs[:20]:
                text += f"🆔 {sub}\n"
            if len(subs) > 20:
                text += f"\n<i>и еще {len(subs)-20}...</i>"
        else:
            text = "Нет подписчиков"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ: полная статистика
    elif call.data == 'admin_stats':
        if user_id != ADMIN_ID:
            return
        subs_count = get_subscriber_count()
        uptime = datetime.now() - bot_start_time
        hours = uptime.seconds // 3600
        days = uptime.days
        
        text = f"<b>📊 ПОЛНАЯ СТАТИСТИКА</b>\n\n"
        text += f"👥 Подписчиков: <b>{subs_count}</b>\n"
        text += f"📡 API статус: <b>{api_status}</b>\n"
        text += f"🕐 Аптайм: <b>{days}д {hours}ч</b>\n"
        text += f"👑 Админ: <b>{ADMIN_ID}</b>\n"
        text += f"📢 Канал: <b>{SOURCE_CHANNEL}</b>"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ: рассылка с кнопкой
    elif call.data == 'admin_post_with_btn':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "<b>📤 РАССЫЛКА С КНОПКОЙ</b>\n\n"
            "Отправь текст поста в формате:\n"
            "<code>/admin_post текст поста | текст кнопки | ссылка</code>\n\n"
            "Пример:\n"
            "<code>/admin_post Новый чит вышел! | Забрать | https://t.me/duckpartner</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ: обычная рассылка
    elif call.data == 'admin_broadcast':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "<b>📨 РАССЫЛКА ВСЕМ</b>\n\n"
            "Отправь текст сообщения для рассылки:\n"
            "<code>/broadcast текст сообщения</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    
    # Админ: проверить новые
    elif call.data == 'admin_check':
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text(
            "🔄 <b>Проверяю новые посты...</b>",
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

# ---------- админ команды ----------
@bot.message_handler(commands=['admin_post'])
def admin_post_with_button(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/admin_post', '', 1).strip()
    if not text:
        bot.reply_to(message, "<b>❌ Используй:</b>\n<code>/admin_post текст | кнопка | ссылка</code>", parse_mode='HTML')
        return
    
    parts = text.split('|')
    if len(parts) < 3:
        bot.reply_to(message, "<b>❌ Неверный формат!</b>\n\nНужно: текст | кнопка | ссылка", parse_mode='HTML')
        return
    
    post_text = parts[0].strip()
    btn_text = parts[1].strip()
    btn_url = parts[2].strip()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(btn_text, url=btn_url))
    
    subscribers = get_all_subscribers()
    if not subscribers:
        bot.reply_to(message, "Нет подписчиков")
        return
    
    bot.reply_to(message, f"📤 Рассылаю {len(subscribers)} подписчикам...")
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(
                user_id,
                f"<b>📢 НОВОСТЬ!</b>\n\n{post_text}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            success += 1
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    bot.send_message(message.chat.id, f"✅ Отправлено: {success}/{len(subscribers)}")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.reply_to(message, "❌ Используй: /broadcast текст сообщения")
        return
    
    subscribers = get_all_subscribers()
    if not subscribers:
        bot.reply_to(message, "Нет подписчиков")
        return
    
    bot.reply_to(message, f"📤 Рассылаю {len(subscribers)} подписчикам...")
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(user_id, text, parse_mode='HTML')
            success += 1
            time.sleep(0.05)
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    bot.send_message(message.chat.id, f"✅ Отправлено: {success}/{len(subscribers)}")

# ---------- рассылка новых постов с кнопками ----------
def send_to_subscribers(post_text, post_link, post_id):
    subscribers = get_all_subscribers()
    if not subscribers:
        return
    
    keyboard = get_post_keyboard(post_link, post_text, post_id)
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"<b>🔔 НОВЫЙ ПОСТ В КАНАЛЕ!</b>\n\n{post_text[:500]}",
                reply_markup=keyboard,
                parse_mode='HTML',
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