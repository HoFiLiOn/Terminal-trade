import sqlite3
import logging
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = '8891687206:AAHUcgCDsiZr5YqQyx4kWPsMWfmw8IttikA'
BOT_NAME = "Vexor Observer"
ADMIN_ID = 8388843828  # ТВОЙ TELEGRAM ID (цифра)
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

# ---------- КНОПКИ ----------
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ ПОДПИСАТЬСЯ", callback_data='subscribe')],
        [InlineKeyboardButton("❌ ОТПИСАТЬСЯ", callback_data='unsubscribe')],
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data='stats')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- КОМАНДЫ ДЛЯ ВСЕХ ----------
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(
        f"👁 {BOT_NAME}\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"Подпишись, чтобы получать новые посты из канала Vexor cheats | News\n\n"
        f"Новые посты будут приходить сюда автоматически, когда админ их отправит.\n\n"
        f"👇 ВЫБЕРИ ДЕЙСТВИЕ:",
        reply_markup=get_main_keyboard()
    )

def button_handler(update: Update, context):
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
            f"📊 СТАТИСТИКА\n\n👀 Подписчиков: {get_subscriber_count()}",
            reply_markup=get_main_keyboard()
        )

# ---------- КОМАНДЫ ДЛЯ АДМИНА ----------
def post(update: Update, context):
    """Отправить пост всем подписчикам - /post текст поста"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Только для админа")
        return
    
    text = ' '.join(context.args)
    if not text:
        update.message.reply_text("❌ Используй: /post текст поста")
        return
    
    subscribers = get_all_subscribers()
    if not subscribers:
        update.message.reply_text("Нет подписчиков")
        return
    
    update.message.reply_text(f"📤 Рассылаю {len(subscribers)} подписчикам...")
    
    success = 0
    for user_id in subscribers:
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"🔔 НОВЫЙ ПОСТ ИЗ КАНАЛА!\n\n{text}"
            )
            success += 1
        except Exception as e:
            if "Forbidden" in str(e):
                remove_subscriber(user_id)
            logger.error(f"Ошибка {user_id}: {e}")
    
    update.message.reply_text(f"✅ Готово! Отправлено: {success}/{len(subscribers)}")

def broadcast(update: Update, context):
    """Отправить любое сообщение всем - /broadcast текст"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Только для админа")
        return
    
    text = ' '.join(context.args)
    if not text:
        update.message.reply_text("❌ Используй: /broadcast текст")
        return
    
    subscribers = get_all_subscribers()
    for user_id in subscribers:
        try:
            context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"Ошибка {user_id}: {e}")
    
    update.message.reply_text("✅ Рассылка завершена")

def subscribers_list(update: Update, context):
    """Показать список подписчиков - /subscribers"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Только для админа")
        return
    
    subscribers = get_all_subscribers()
    text = f"👀 Подписчики ({len(subscribers)}):\n"
    text += ', '.join(map(str, subscribers)) if subscribers else "нет"
    update.message.reply_text(text)

# ---------- ЗАПУСК ----------
def main():
    init_db()
    
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    # Команды для всех
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # Команды для админа
    dp.add_handler(CommandHandler('post', post))
    dp.add_handler(CommandHandler('broadcast', broadcast))
    dp.add_handler(CommandHandler('subscribers', subscribers_list))
    
    logger.info(f"✅ Бот запущен! Админ: {ADMIN_ID}")
    logger.info("Доступные команды:")
    logger.info("  /start - главное меню")
    logger.info("  /post ТЕКСТ - отправить пост всем подписчикам")
    logger.info("  /broadcast ТЕКСТ - отправить любое сообщение всем")
    logger.info("  /subscribers - список подписчиков")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")