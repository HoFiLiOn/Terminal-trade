import telebot
from telebot import types
import random
import json
import os
from datetime import datetime

# ========== ТОКЕН ==========
TOKEN = "8412567351:AAG7eEMXlNfDBsNZF08GD-Pr-LH-2z1txSQ"
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ФАЙЛЫ БАЗЫ ДАННЫХ ==========
USERS_DIR = "users"
LEADERBOARD_FILE = "leaderboard.json"
PROMOCODES_FILE = "promocodes.json"

# Создаем папку для пользователей
if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== ДАННЫЕ ПО УМОЛЧАНИЮ ==========
DEFAULT_COMPANIES = {
    'AAPL': {'name': 'Apple Inc.', 'price': 175.50},
    'MSFT': {'name': 'Microsoft Corp.', 'price': 330.25},
    'GOOG': {'name': 'Alphabet (Google)', 'price': 2800.75},
    'AMZN': {'name': 'Amazon.com Inc.', 'price': 3450.00},
    'TSLA': {'name': 'Tesla Inc.', 'price': 900.50},
    'META': {'name': 'Meta Platforms', 'price': 310.80},
    'NVDA': {'name': 'NVIDIA Corp.', 'price': 890.60},
    'JPM': {'name': 'JPMorgan Chase', 'price': 150.30},
    'JNJ': {'name': 'Johnson & Johnson', 'price': 160.40},
    'WMT': {'name': 'Walmart Inc.', 'price': 145.20}
}

# ========== ПРОМОКОДЫ ==========
PROMOCODES = {
    "WELCOME100": {"bonus": 100, "max_uses": 10, "used_count": 0},
    "BONUS500": {"bonus": 500, "max_uses": 10, "used_count": 0},
    "START1000": {"bonus": 1000, "max_uses": 10, "used_count": 0}
}

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С JSON ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ИГРОКАМИ ==========
def get_user_file(user_id):
    return os.path.join(USERS_DIR, f"{user_id}.json")

def load_user(user_id):
    user_file = get_user_file(user_id)
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'prev_prices' not in data:
                data['prev_prices'] = {}
            return data
    else:
        return {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'companies': DEFAULT_COMPANIES.copy(),
            'prev_prices': {},
            'username': None,
            'used_promos': []
        }

def save_user(user_id, data):
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== ФУНКЦИИ ИГРЫ ==========
def change_prices(user_data):
    for ticker in user_data['companies']:
        old_price = user_data['companies'][ticker]['price']
        change = random.uniform(-0.05, 0.05)
        new_price = old_price * (1 + change)
        user_data['companies'][ticker]['price'] = round(new_price, 2)
        user_data['prev_prices'][ticker] = round(old_price, 2)

def get_price_change(old_price, new_price):
    if old_price == 0:
        return "0.00%"
    change = ((new_price - old_price) / old_price) * 100
    return f"{change:+.2f}%"

def buy_stock(user_data, ticker, amount):
    if ticker not in user_data['companies']:
        return False, "❌ Нет такой компании"
    
    price = user_data['companies'][ticker]['price']
    total = price * amount
    
    if user_data['money'] >= total:
        user_data['money'] -= total
        user_data['money'] = round(user_data['money'], 2)
        
        if ticker in user_data['portfolio']:
            user_data['portfolio'][ticker] += amount
        else:
            user_data['portfolio'][ticker] = amount
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"❌ Недостаточно денег. Нужно ${total:,.2f}"

def sell_stock(user_data, ticker, amount):
    if ticker not in user_data['portfolio']:
        return False, "❌ У вас нет таких акций"
    
    if user_data['portfolio'][ticker] >= amount:
        price = user_data['companies'][ticker]['price']
        total = price * amount
        user_data['money'] += total
        user_data['money'] = round(user_data['money'], 2)
        user_data['portfolio'][ticker] -= amount
        
        if user_data['portfolio'][ticker] == 0:
            del user_data['portfolio'][ticker]
        
        return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"❌ У вас только {user_data['portfolio'][ticker]} акций"

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📊 Мой статус")
    btn2 = types.KeyboardButton("📈 Список компаний")
    btn3 = types.KeyboardButton("⏩ Следующий день")
    btn4 = types.KeyboardButton("🏆 Таблица лидеров")
    btn5 = types.KeyboardButton("🔄 Новая игра")
    btn6 = types.KeyboardButton("🎟️ Промокод")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user_data = load_user(int(user_id))
    user_data['username'] = username
    save_user(int(user_id), user_data)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {username}! 👋

💰 Стартовый капитал: $1000

Как играть:
• buy AAPL 5 — купить
• sell TSLA 2 — продать
• next — следующий день
• /promo КОД — промокод
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    total = user_data['money']
    for ticker, amount in user_data['portfolio'].items():
        total += amount * user_data['companies'][ticker]['price']
    total = round(total, 2)
    
    text = f"""
📊 ТВОЙ СТАТУС (День {user_data['day']})

💰 Баланс: ${user_data['money']:,.2f}
💵 Капитал: ${total:,.2f}

📋 Портфель:
    """
    
    if user_data['portfolio']:
        for ticker, amount in user_data['portfolio'].items():
            price = user_data['companies'][ticker]['price']
            value = amount * price
            text += f"\n{ticker}: {amount} шт. (${value:,.2f})"
    else:
        text += "\nУ вас пока нет акций"
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['list'])
def list_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    text = f"📋 ВСЕ КОМПАНИИ (День {user_data['day']})\n\n"
    
    for ticker, data in user_data['companies'].items():
        old_price = user_data['prev_prices'].get(ticker, data['price'])
        change = get_price_change(old_price, data['price'])
        
        if change.startswith('+'):
            emoji = "🟢"
        elif change.startswith('-'):
            emoji = "🔴"
        else:
            emoji = "⚪"
        
        text += f"{ticker} — {data['name']}\n"
        text += f"💰 ${data['price']:,.2f} {emoji} {change}\n\n"
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['next'])
def next_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    change_prices(user_data)
    user_data['day'] += 1
    save_user(user_id, user_data)
    
    text = f"⏩ День {user_data['day']}\n\nЦены обновлены!"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['reset'])
def reset_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user_data = {
        'money': 1000.0,
        'portfolio': {},
        'day': 1,
        'companies': DEFAULT_COMPANIES.copy(),
        'prev_prices': {},
        'username': username,
        'used_promos': []
    }
    save_user(user_id, user_data)
    
    text = "🔄 Новая игра! Ты начинаешь заново с $1000"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['promo'])
def promo_command(message):
    user_id = str(message.from_user.id)
    user_data = load_user(int(user_id))
    
    try:
        promo = message.text.split()[1].upper()
        
        if promo in PROMOCODES:
            promo_data = PROMOCODES[promo]
            
            if promo_data['used_count'] >= promo_data['max_uses']:
                bot.reply_to(message, "❌ Промокод закончился")
                return
            
            if promo in user_data.get('used_promos', []):
                bot.reply_to(message, "❌ Ты уже активировал этот промокод")
                return
            
            user_data['money'] += promo_data['bonus']
            user_data['money'] = round(user_data['money'], 2)
            if 'used_promos' not in user_data:
                user_data['used_promos'] = []
            user_data['used_promos'].append(promo)
            
            promo_data['used_count'] += 1
            
            # Сохраняем обновленные промокоды
            save_json(PROMOCODES_FILE, PROMOCODES)
            save_user(int(user_id), user_data)
            
            bot.reply_to(message, f"✅ Промокод активирован! +${promo_data['bonus']}")
        else:
            bot.reply_to(message, "❌ Неверный промокод")
            
    except IndexError:
        bot.reply_to(message, "❌ Использование: /promo КОД")

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
📚 ПОМОЩЬ

Кнопки:
• Мой статус — баланс и портфель
• Список компаний — все цены
• Следующий день — новый день
• Новая игра — начать заново
• Промокод — активировать бонус

Команды:
buy AAPL 5 — купить 5 акций Apple
sell TSLA 2 — продать 2 акции Tesla
/promo КОД — активировать промокод
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ========== ОБРАБОТКА КНОПОК ==========
@bot.message_handler(func=lambda message: message.text in ["📊 Мой статус", "📈 Список компаний", "⏩ Следующий день", "🏆 Таблица лидеров", "🔄 Новая игра", "🎟️ Промокод"])
def button_handler(message):
    if message.text == "📊 Мой статус":
        status_command(message)
    elif message.text == "📈 Список компаний":
        list_command(message)
    elif message.text == "⏩ Следующий день":
        next_command(message)
    elif message.text == "🔄 Новая игра":
        reset_command(message)
    elif message.text == "🎟️ Промокод":
        bot.send_message(message.chat.id, "Введи /promo КОД")

# ========== ОБРАБОТКА ПОКУПКИ/ПРОДАЖИ ==========
@bot.message_handler(func=lambda message: message.text.lower().startswith(('buy ', 'sell ')))
def trade_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    try:
        parts = message.text.split()
        command = parts[0].lower()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        if command == 'buy':
            success, msg = buy_stock(user_data, ticker, amount)
        elif command == 'sell':
            success, msg = sell_stock(user_data, ticker, amount)
        else:
            return
        
        if success:
            save_user(user_id, user_data)
        
        bot.send_message(message.chat.id, msg, reply_markup=main_menu())
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Формат: buy AAPL 5 или sell TSLA 2", reply_markup=main_menu())

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trader запущен...")
    print("Бот готов к работе!")
    bot.infinity_polling()