import telebot
from telebot import types
import random
import json
import os
from datetime import datetime, timedelta
from flask import Flask
import threading
import time

# ========== ТОКЕН ==========
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ФАЙЛЫ БАЗЫ ДАННЫХ ==========
USERS_DIR = "users"
LEADERBOARD_FILE = "leaderboard.json"
PROMOCODES_FILE = "promocodes.json"
SEASON_FILE = "season.json"

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
    "START1000": {"bonus": 1000, "max_uses": 10, "used_count": 0},
    "LUCKY200": {"bonus": 200, "max_uses": 10, "used_count": 0},
    "TRADER50": {"bonus": 50, "max_uses": 10, "used_count": 0},
    "INVEST300": {"bonus": 300, "max_uses": 10, "used_count": 0},
    "CAPITAL250": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "MONEY150": {"bonus": 150, "max_uses": 10, "used_count": 0},
    "PROFIT400": {"bonus": 400, "max_uses": 10, "used_count": 0},
    "GAIN350": {"bonus": 350, "max_uses": 10, "used_count": 0},
    "AAPL50": {"bonus": 50, "max_uses": 10, "used_count": 0},
    "TSLA100": {"bonus": 100, "max_uses": 10, "used_count": 0},
    "NVDA200": {"bonus": 200, "max_uses": 10, "used_count": 0},
    "GOOG150": {"bonus": 150, "max_uses": 10, "used_count": 0},
    "META75": {"bonus": 75, "max_uses": 10, "used_count": 0},
    "AMZN125": {"bonus": 125, "max_uses": 10, "used_count": 0},
    "MSFT175": {"bonus": 175, "max_uses": 10, "used_count": 0},
    "JPM80": {"bonus": 80, "max_uses": 10, "used_count": 0},
    "JNJ90": {"bonus": 90, "max_uses": 10, "used_count": 0},
    "WMT60": {"bonus": 60, "max_uses": 10, "used_count": 0},
    "SPRING25": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "SUMMER25": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "AUTUMN25": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "WINTER25": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "CRYPTO500": {"bonus": 500, "max_uses": 10, "used_count": 0},
    "BITCOIN250": {"bonus": 250, "max_uses": 10, "used_count": 0},
    "ETHEREUM150": {"bonus": 150, "max_uses": 10, "used_count": 0},
    "DOGECOIN50": {"bonus": 50, "max_uses": 10, "used_count": 0},
    "SOLANA100": {"bonus": 100, "max_uses": 10, "used_count": 0},
    "BINANCE200": {"bonus": 200, "max_uses": 10, "used_count": 0},
    "COINBASE125": {"bonus": 125, "max_uses": 10, "used_count": 0},
    "BYBIT175": {"bonus": 175, "max_uses": 10, "used_count": 0},
    "OKX225": {"bonus": 225, "max_uses": 10, "used_count": 0},
    "KRAKEN275": {"bonus": 275, "max_uses": 10, "used_count": 0},
    "HUOBI325": {"bonus": 325, "max_uses": 10, "used_count": 0},
    "GATEIO375": {"bonus": 375, "max_uses": 10, "used_count": 0},
    "MEXC425": {"bonus": 425, "max_uses": 10, "used_count": 0},
    "BITGET475": {"bonus": 475, "max_uses": 10, "used_count": 0},
    "KUCION525": {"bonus": 525, "max_uses": 10, "used_count": 0},
    "POLONIEX575": {"bonus": 575, "max_uses": 10, "used_count": 0},
    "BITTREX625": {"bonus": 625, "max_uses": 10, "used_count": 0},
    "HITBTC675": {"bonus": 675, "max_uses": 10, "used_count": 0},
    "CEXIO725": {"bonus": 725, "max_uses": 10, "used_count": 0},
    "BANK1000": {"bonus": 1000, "max_uses": 10, "used_count": 0}
}

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run_web, daemon=True).start()

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
            'first_seen': str(datetime.now()),
            'used_promos': []
        }

def save_user(user_id, data):
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    update_leaderboard(user_id, data)

# ========== СЕЗОНЫ ==========
def init_season():
    season_data = load_json(SEASON_FILE)
    if not season_data:
        season_data = {
            'season': 1,
            'name': 'ВЕСНА',
            'start': str(datetime.now()),
            'end': str(datetime.now() + timedelta(days=14)),
            'active': True
        }
        save_json(SEASON_FILE, season_data)
    return season_data

def check_season_end():
    season_data = load_json(SEASON_FILE)
    if not season_data:
        return
    
    end_date = datetime.fromisoformat(season_data['end'])
    if datetime.now() > end_date and season_data['active']:
        # Вайп всех данных
        for filename in os.listdir(USERS_DIR):
            file_path = os.path.join(USERS_DIR, filename)
            os.remove(file_path)
        
        # Очищаем таблицу лидеров
        if os.path.exists(LEADERBOARD_FILE):
            os.remove(LEADERBOARD_FILE)
        
        # Новый сезон
        season_data['active'] = False
        save_json(SEASON_FILE, season_data)

def season_check_loop():
    while True:
        time.sleep(3600)  # Проверка каждый час
        check_season_end()

threading.Thread(target=season_check_loop, daemon=True).start()

init_season()

# ========== ТАБЛИЦА ЛИДЕРОВ ==========
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def calculate_total_capital(user_data):
    total = user_data['money']
    for ticker, amount in user_data['portfolio'].items():
        total += amount * user_data['companies'][ticker]['price']
    return round(total, 2)

def update_leaderboard(user_id, user_data):
    leaderboard = load_leaderboard()
    capital = calculate_total_capital(user_data)
    username = user_data.get('username') or f"Player_{user_id}"
    
    found = False
    for entry in leaderboard:
        if entry['user_id'] == user_id:
            if capital > entry['capital']:
                entry['capital'] = capital
                entry['day'] = user_data['day']
                entry['last_update'] = str(datetime.now())
            found = True
            break
    
    if not found:
        leaderboard.append({
            'user_id': user_id,
            'username': username,
            'capital': capital,
            'day': user_data['day'],
            'first_seen': user_data.get('first_seen', str(datetime.now())),
            'last_update': str(datetime.now())
        })
    
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, indent=2, ensure_ascii=False)

def get_leaderboard_text():
    leaderboard = load_leaderboard()
    season_data = load_json(SEASON_FILE)
    
    if not leaderboard:
        return "Таблица лидеров пока пуста. Играй и стань первым!"
    
    end_date = datetime.fromisoformat(season_data['end'])
    days_left = (end_date - datetime.now()).days
    hours_left = ((end_date - datetime.now()).seconds // 3600)
    
    text = f"🏆 ТАБЛИЦА ЛИДЕРОВ\n"
    text += f"Сезон: {season_data['name']}\n"
    text += f"До конца: {days_left}д {hours_left}ч\n\n"
    
    for i, entry in enumerate(leaderboard[:10], 1):
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        name = entry['username']
        if len(name) > 15:
            name = name[:12] + "..."
        
        text += f"{medal} {name} — ${entry['capital']:,.2f}\n"
    
    text += f"\nВсего трейдеров: {len(leaderboard)}"
    return text

def leaderboard_update_loop():
    while True:
        time.sleep(300)  # 5 минут
        leaderboard = load_leaderboard()
        if leaderboard:
            leaderboard.sort(key=lambda x: x['capital'], reverse=True)
            with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
                json.dump(leaderboard, f, indent=2, ensure_ascii=False)

threading.Thread(target=leaderboard_update_loop, daemon=True).start()

# ========== ПРОМОКОДЫ ==========
def load_promocodes():
    if os.path.exists(PROMOCODES_FILE):
        with open(PROMOCODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return PROMOCODES.copy()

def save_promocodes(promos):
    with open(PROMOCODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(promos, f, indent=2, ensure_ascii=False)

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
        return False, "Нет такой компании"
    
    price = user_data['companies'][ticker]['price']
    total = price * amount
    
    if user_data['money'] >= total:
        user_data['money'] -= total
        if ticker in user_data['portfolio']:
            user_data['portfolio'][ticker] += amount
        else:
            user_data['portfolio'][ticker] = amount
        return True, f"Куплено {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"Недостаточно денег. Нужно ${total:,.2f}"

def sell_stock(user_data, ticker, amount):
    if ticker not in user_data['portfolio']:
        return False, "У вас нет таких акций"
    
    if user_data['portfolio'][ticker] >= amount:
        price = user_data['companies'][ticker]['price']
        total = price * amount
        user_data['money'] += total
        user_data['portfolio'][ticker] -= amount
        
        if user_data['portfolio'][ticker] == 0:
            del user_data['portfolio'][ticker]
        
        return True, f"Продано {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"У вас только {user_data['portfolio'][ticker]} акций"

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
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user_data = load_user(user_id)
    user_data['username'] = username
    save_user(user_id, user_data)
    
    season_data = load_json(SEASON_FILE)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
║    Биржевой симулятор в TG    ║
╚══════════════════════════════╝

Привет, {username}! 👋

Сезон: {season_data['name']}
Стартовый капитал: $1000

Как играть:
• buy AAPL 5 — купить
• sell TSLA 2 — продать
• next — следующий день
• /promo КОД — активировать промокод
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['leaderboard'])
def leaderboard_command(message):
    text = get_leaderboard_text()
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    capital = calculate_total_capital(user_data)
    
    text = f"""
📊 ТВОЙ СТАТУС (День {user_data['day']})

💰 Баланс: ${user_data['money']:,.2f}
💵 Капитал: ${capital:,.2f}

📋 Портфель:
    """
    
    if user_data['portfolio']:
        for ticker, amount in user_data['portfolio'].items():
            price = user_data['companies'][ticker]['price']
            value = amount * price
            text += f"\n{ticker}: {amount} шт. (${value:,.2f})"
    else:
        text += "\nУ вас пока нет акций"
    
    leaderboard = load_leaderboard()
    for i, entry in enumerate(leaderboard, 1):
        if entry['user_id'] == user_id:
            text += f"\n\nМесто: {i} из {len(leaderboard)}"
            break
    
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
        'first_seen': str(datetime.now()),
        'used_promos': []
    }
    save_user(user_id, user_data)
    
    text = "🔄 Новая игра!\nТы начинаешь заново с $1000"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['promo'])
def promo_command(message):
    user_id = str(message.from_user.id)
    user_data = load_user(int(user_id))
    
    try:
        promo = message.text.split()[1].upper()
        promos = load_promocodes()
        
        if promo in promos:
            promo_data = promos[promo]
            
            if promo_data['used_count'] >= promo_data['max_uses']:
                bot.reply_to(message, "❌ Промокод закончился")
                return
            
            if promo in user_data.get('used_promos', []):
                bot.reply_to(message, "❌ Ты уже активировал этот промокод")
                return
            
            user_data['money'] += promo_data['bonus']
            if 'used_promos' not in user_data:
                user_data['used_promos'] = []
            user_data['used_promos'].append(promo)
            
            promo_data['used_count'] += 1
            save_promocodes(promos)
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
• Список компаний — все цены с изменениями
• Следующий день — новый день
• Таблица лидеров — рейтинг игроков
• Новая игра — начать заново
• Промокод — активировать бонус

Команды:
buy AAPL 5 — купить 5 акций Apple
sell TSLA 2 — продать 2 акции Tesla
/promo КОД — активировать промокод
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['addpromo'])
def add_promo_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        promo = parts[1].upper()
        bonus = int(parts[2])
        max_uses = int(parts[3])
        
        promos = load_promocodes()
        promos[promo] = {
            "bonus": bonus,
            "max_uses": max_uses,
            "used_count": 0
        }
        save_promocodes(promos)
        
        bot.reply_to(message, f"✅ Промокод {promo} добавлен (${bonus}, {max_uses} использований)")
    except:
        bot.reply_to(message, "❌ Использование: /addpromo КОД БОНУС МАКС_ИСПОЛЬЗОВАНИЙ")

@bot.message_handler(commands=['stats'])
def stats_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total_users = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
    leaderboard = load_leaderboard()
    promos = load_promocodes()
    
    total_promo_uses = sum(p['used_count'] for p in promos.values())
    
    text = f"""
📊 АДМИН СТАТИСТИКА

👥 Всего игроков: {total_users}
🏆 В лидерборде: {len(leaderboard)}
🎟️ Промокодов активировано: {total_promo_uses}
    """
    bot.send_message(message.chat.id, text)

# ========== ОБРАБОТКА КНОПОК ==========
@bot.message_handler(func=lambda message: message.text in ["📊 Мой статус", "📈 Список компаний", "⏩ Следующий день", "🏆 Таблица лидеров", "🔄 Новая игра", "🎟️ Промокод"])
def button_handler(message):
    if message.text == "📊 Мой статус":
        status_command(message)
    elif message.text == "📈 Список компаний":
        list_command(message)
    elif message.text == "⏩ Следующий день":
        next_command(message)
    elif message.text == "🏆 Таблица лидеров":
        leaderboard_command(message)
    elif message.text == "🔄 Новая игра":
        reset_command(message)
    elif message.text == "🎟️ Промокод":
        msg = bot.send_message(message.chat.id, "Введи промокод:")
        bot.register_next_step_handler(msg, process_promo_input)

def process_promo_input(message):
    promo = message.text.upper()
    user_id = str(message.from_user.id)
    user_data = load_user(int(user_id))
    
    promos = load_promocodes()
    
    if promo in promos:
        promo_data = promos[promo]
        
        if promo_data['used_count'] >= promo_data['max_uses']:
            bot.reply_to(message, "❌ Промокод закончился")
            return
        
        if promo in user_data.get('used_promos', []):
            bot.reply_to(message, "❌ Ты уже активировал этот промокод")
            return
        
        user_data['money'] += promo_data['bonus']
        if 'used_promos' not in user_data:
            user_data['used_promos'] = []
        user_data['used_promos'].append(promo)
        
        promo_data['used_count'] += 1
        save_promocodes(promos)
        save_user(int(user_id), user_data)
        
        bot.reply_to(message, f"✅ Промокод активирован! +${promo_data['bonus']}")
    else:
        bot.reply_to(message, "❌ Неверный промокод")

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
    print("🤖 Terminal Trader с сезонами и промокодами запущен...")
    bot.infinity_polling()