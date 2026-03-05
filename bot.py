import telebot
from telebot import types
import os

# ========== ТОКЕН ==========
TOKEN = "8740420404:AAHli4wJgrgiAKtXeAC7GreL-rtyc2OwMgo"
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ССЫЛКИ НА ИЗОБРАЖЕНИЯ ==========
# СЮДА ВСТАВЛЯЙ СВОИ ССЫЛКИ
IMAGES = {
    'logo': 'https://telegra.ph/file/ваша-ссылка-1.jpg',
    'welcome': 'https://telegra.ph/file/ваша-ссылка-2.jpg',
    'shop': 'https://telegra.ph/file/ваша-ссылка-3.jpg',
    'leaderboard': 'https://telegra.ph/file/ваша-ссылка-4.jpg',
    'promo': 'https://telegra.ph/file/ваша-ссылка-5.jpg'
}

# ========== КОМАНДА СТАРТ С КАРТИНКОЙ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    # Отправляем фото с подписью
    if IMAGES.get('welcome'):
        bot.send_photo(
            message.chat.id,
            IMAGES['welcome'],
            caption="👋 Добро пожаловать в тестового бота!\n\nИспользуй кнопки ниже:"
        )
    else:
        bot.send_message(message.chat.id, "👋 Добро пожаловать!")

# ========== КОМАНДА С ЛОГОТИПОМ ==========
@bot.message_handler(commands=['logo'])
def logo_command(message):
    if IMAGES.get('logo'):
        bot.send_photo(
            message.chat.id,
            IMAGES['logo'],
            caption="🔥 Наш логотип"
        )
    else:
        bot.reply_to(message, "Логотип не загружен")

# ========== КОМАНДА МАГАЗИН С КАРТИНКОЙ ==========
@bot.message_handler(commands=['shop'])
def shop_command(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🛒 Купить VIP", callback_data="buy_vip")
    btn2 = types.InlineKeyboardButton("🛒 Купить Легенд", callback_data="buy_legend")
    markup.add(btn1, btn2)
    
    if IMAGES.get('shop'):
        bot.send_photo(
            message.chat.id,
            IMAGES['shop'],
            caption="🛒 Добро пожаловать в магазин!\nВыбери товар:",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "🛒 Магазин временно недоступен")

# ========== КОМАНДА ЛИДЕРЫ С КАРТИНКОЙ ==========
@bot.message_handler(commands=['top'])
def top_command(message):
    if IMAGES.get('leaderboard'):
        bot.send_photo(
            message.chat.id,
            IMAGES['leaderboard'],
            caption="🏆 Таблица лидеров\n\n1. @user1 — 5000$\n2. @user2 — 4500$\n3. @user3 — 4000$"
        )
    else:
        bot.send_message(message.chat.id, "🏆 Таблица лидеров временно недоступна")

# ========== КОМАНДА ПРОМО С КАРТИНКОЙ ==========
@bot.message_handler(commands=['promo'])
def promo_command(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🎟️ Активировать", callback_data="activate_promo")
    markup.add(btn)
    
    if IMAGES.get('promo'):
        bot.send_photo(
            message.chat.id,
            IMAGES['promo'],
            caption="🎁 Введи промокод командой /code НАЗВАНИЕ",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "🎁 Промокоды временно недоступны")

# ========== ТЕСТОВАЯ КОМАНДА ДЛЯ ПРОВЕРКИ ССЫЛОК ==========
@bot.message_handler(commands=['testimg'])
def testimg_command(message):
    """Проверяет все ссылки на изображения"""
    text = "🔍 **ПРОВЕРКА ИЗОБРАЖЕНИЙ**\n\n"
    
    for name, url in IMAGES.items():
        try:
            bot.send_chat_action(message.chat.id, 'upload_photo')
            text += f"✅ {name}: ссылка работает\n"
        except:
            text += f"❌ {name}: ссылка не работает\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ========== АДМИН-КОМАНДА ДЛЯ ДОБАВЛЕНИЯ ССЫЛОК ==========
@bot.message_handler(commands=['setimg'])
def setimg_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        name = parts[1]
        url = parts[2]
        
        IMAGES[name] = url
        bot.reply_to(message, f"✅ Изображение {name} сохранено")
    except:
        bot.reply_to(message, "❌ Использование: /setimg НАЗВАНИЕ ССЫЛКА")

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "buy_vip":
        bot.answer_callback_query(call.id, "✅ Ты купил VIP!", show_alert=True)
    elif call.data == "buy_legend":
        bot.answer_callback_query(call.id, "✅ Ты купил Легенд!", show_alert=True)
    elif call.data == "activate_promo":
        bot.answer_callback_query(call.id, "🎟️ Введи промокод: /code НАЗВАНИЕ")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Тестовый бот с изображениями запущен...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("\n📌 КОМАНДЫ:")
    print("/start — приветствие с картинкой")
    print("/logo — показать логотип")
    print("/shop — магазин с картинкой")
    print("/top — таблица лидеров с картинкой")
    print("/promo — промокоды с картинкой")
    print("/testimg — проверить ссылки")
    print("/setimg НАЗВАНИЕ ССЫЛКА — добавить картинку (только админ)")
    
    bot.infinity_polling()