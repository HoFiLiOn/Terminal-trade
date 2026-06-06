import sqlite3
import logging
import sys
import telebot
from telebot import types

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
BOT_NAME = "Vexor Observer"
ADMIN_ID = 8388843828  # ТВОЙ TELEGRAM ID
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

# ---------- КНОПКИ ----------
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_subscribe = types.InlineKeyboardButton("✅ ПОДПИСАТЬСЯ", callback_data='subscribe')
    btn_unsubscribe = types.InlineKeyboardButton("❌ ОТПИСАТЬСЯ", callback_data='unsubscribe')
    btn_stats = types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data='stats')
    keyboard.add(btn_subscribe, btn_unsubscribe)
    keyboard.add(btn_stats)
    return keyboard

# ---------- КОМАНДЫ ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.send_message(
        message.chat.id,
        f"👁 {BOT_NAME}\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"Подпишись, чтобы получать новые посты из канала Vexor cheats | News\n\n"
        f"Новые посты будут приходить сюда, когда админ их отправит.\n\n"
        f"👇 ВЫБЕРИ ДЕЙСТВИЕ:",
        reply_markup=get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == 'subscribe':
        add_subscriber(user_id)
        bot.edit_message_text(
            f"✅ ПОДПИСАН!\n\n👀 Подписчиков: {get_subscriber_count()}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    elif call.data == 'unsubscribe':
        remove_subscriber(user_id)
        bot.edit_message_text(
            "❌ ОТПИСАН",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    elif call.data == 'stats':
        bot.edit_message_text(
            f"📊 СТАТИСТИКА\n\n👀 Подписчиков: {get_subscriber_count()}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    bot.answer_callback_query(call.id)

# ---------- КОМАНДЫ АДМИНА ----------
@bot.message_handler(commands=['post'])
def post(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только для админа")
        return
    
    text = message.text.replace('/post', '', 1).strip()
    if not text:
        bot.reply_to(message, "❌ Используй: /post текст поста")
        return
    
    subscribers = get_all_subscribers()
    if not subscribers:
        bot.reply_to(message, "Нет подписчиков")
        return
    
    bot.reply_to(message, f"📤 Рассылаю {len(subscribers)} подписчикам...")
    
    success = 0
    for user_id in subscribers:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"🔔 НОВЫЙ ПОСТ ИЗ КАНАЛА!\n\n{text}"
            )
            success += 1
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    bot.send_message(message.chat.id, f"✅ Готово! Отправлено: {success}/{len(subscribers)}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только для админа")
        return
    
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.reply_to(message, "❌ Используй: /broadcast текст")
        return
    
    subscribers = get_all_subscribers()
    for user_id in subscribers:
        try:
            bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"Ошибка {user_id}: {e}")
    
    bot.reply_to(message, "✅ Рассылка завершена")

@bot.message_handler(commands=['subscribers'])
def subscribers_list(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только для админа")
        return
    
    subscribers = get_all_subscribers()
    text = f"👀 Подписчики ({len(subscribers)}):\n"
    text += ', '.join(map(str, subscribers)) if subscribers else "нет"
    bot.reply_to(message, text)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, 
        "📋 ДОСТУПНЫЕ КОМАНДЫ:\n\n"
        "/start - Главное меню\n"
        "/subscribe - Подписаться\n"
        "/unsubscribe - Отписаться\n"
        "/stats - Статистика\n\n"
        "👑 АДМИН КОМАНДЫ:\n"
        "/post ТЕКСТ - Отправить пост всем\n"
        "/broadcast ТЕКСТ - Массовая рассылка\n"
        "/subscribers - Список подписчиков"
    )

@bot.message_handler(commands=['subscribe'])
def subscribe_cmd(message):
    user_id = message.from_user.id
    add_subscriber(user_id)
    bot.reply_to(message, f"✅ ПОДПИСАН!\n\n👀 Подписчиков: {get_subscriber_count()}")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_cmd(message):
    user_id = message.from_user.id
    remove_subscriber(user_id)
    bot.reply_to(message, "❌ ОТПИСАН")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    bot.reply_to(message, f"📊 СТАТИСТИКА\n\n👀 Подписчиков: {get_subscriber_count()}")

# ---------- ЗАПУСК ----------
def main():
    init_db()
    logger.info(f"✅ Бот запущен! Админ: {ADMIN_ID}")
    logger.info("Доступные команды: /start, /post, /broadcast, /subscribers")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")