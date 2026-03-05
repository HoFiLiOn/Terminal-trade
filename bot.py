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
TOKEN = os.environ.get('8740420404:AAHli4wJgrgiAKtXeAC7GreL-rtyc2OwMgo')
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ФАЙЛЫ БАЗЫ ДАННЫХ ==========
USERS_DIR = "users"
LEADERBOARD_FILE = "leaderboard.json"
PROMOCODES_FILE = "promocodes.json"
SEASON_FILE = "season.json"
MESSAGES_FILE = "messages.json"
BANNED_FILE = "banned.json"

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
    'NFLX': {'name': 'Netflix Inc.', 'price': 450.30},
    'DIS': {'name': 'Walt Disney Co.', 'price': 110.20},
    'PYPL': {'name': 'PayPal Holdings', 'price': 85.40},
    'ADBE': {'name': 'Adobe Inc.', 'price': 520.10},
    'AMD': {'name': 'AMD Inc.', 'price': 140.60}
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

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БАНАМИ ==========
def load_banned():
    return load_json(BANNED_FILE)

def save_banned(banned):
    save_json(BANNED_FILE, banned)

def is_banned(user_id):
    banned = load_banned()
    return str(user_id) in banned

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ ==========
def load_messages():
    return load_json(MESSAGES_FILE)

def save_message_owner(message_id, user_id):
    messages = load_messages()
    messages[str(message_id)] = user_id
    save_json(MESSAGES_FILE, messages)

def get_message_owner(message_id):
    messages = load_messages()
    return messages.get(str(message_id))

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ИГРОКАМИ ==========
def get_user_file(user_id):
    return os.path.join(USERS_DIR, f"{user_id}.json")

def load_user(user_id):
    if is_banned(user_id):
        return None
    
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
    if is_banned(user_id):
        return
    
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    update_leaderboard(user_id, data)

# ========== СЕЗОНЫ ==========
last_leaderboard_update = None

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
        for filename in os.listdir(USERS_DIR):
            file_path = os.path.join(USERS_DIR, filename)
            os.remove(file_path)
        
        if os.path.exists(LEADERBOARD_FILE):
            os.remove(LEADERBOARD_FILE)
        
        season_data['active'] = False
        save_json(SEASON_FILE, season_data)

def season_check_loop():
    while True:
        time.sleep(3600)
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
    if not user_data:
        return 0
    total = user_data['money']
    for ticker, amount in user_data['portfolio'].items():
        total += amount * user_data['companies'][ticker]['price']
    return round(total, 2)

def update_leaderboard(user_id, user_data):
    global last_leaderboard_update
    last_leaderboard_update = datetime.now()
    
    if not user_data:
        return
    
    leaderboard = load_leaderboard()
    capital = calculate_total_capital(user_data)
    username = user_data.get('username') or f"Player_{user_id}"
    
    # Обрезаем длинные имена
    if len(username) > 15:
        username = username[:12] + "..."
    
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
    
    # Сортируем и оставляем топ-50
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    leaderboard = leaderboard[:50]
    
    save_json(LEADERBOARD_FILE, leaderboard)

def get_time_since_update():
    global last_leaderboard_update
    if not last_leaderboard_update:
        return "никогда"
    
    diff = datetime.now() - last_leaderboard_update
    if diff.seconds < 60:
        return "только что"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60} мин назад"
    else:
        return f"{diff.seconds // 3600} ч назад"

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
    text += f"До конца: {days_left}д {hours_left}ч\n"
    text += f"🔄 Обновлено: {get_time_since_update()}\n\n"
    
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
        text += f"{medal} {name} — ${entry['capital']:,.2f}\n"
    
    text += f"\nВсего трейдеров: {len(leaderboard)}"
    return text

def force_update_leaderboard():
    global last_leaderboard_update
    last_leaderboard_update = datetime.now()
    
    leaderboard = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = filename.replace('.json', '')
            user_data = load_user(int(user_id))
            if user_data:
                capital = calculate_total_capital(user_data)
                username = user_data.get('username') or f"Player_{user_id}"
                if len(username) > 15:
                    username = username[:12] + "..."
                
                leaderboard.append({
                    'user_id': int(user_id),
                    'username': username,
                    'capital': capital,
                    'day': user_data['day'],
                    'first_seen': user_data.get('first_seen', str(datetime.now())),
                    'last_update': str(datetime.now())
                })
    
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    leaderboard = leaderboard[:50]
    save_json(LEADERBOARD_FILE, leaderboard)

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
    if not user_data:
        return
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
    if not user_data:
        return False, "❌ Ошибка загрузки"
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
    if not user_data:
        return False, "❌ Ошибка загрузки"
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

# ========== INLINE КНОПКИ ==========
def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📊 Статус", callback_data="status")
    btn2 = types.InlineKeyboardButton("📈 Компании", callback_data="list")
    btn3 = types.InlineKeyboardButton("⏩ Next", callback_data="next")
    btn4 = types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard")
    btn5 = types.InlineKeyboardButton("🔄 Сброс", callback_data="reset")
    btn6 = types.InlineKeyboardButton("🎟️ Промо", callback_data="promo")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")
    markup.add(btn)
    return markup

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['trade'])
def start_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
    user_data['username'] = username
    save_user(user_id, user_data)
    
    season_data = load_json(SEASON_FILE)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {username}! 👋

Сезон: {season_data['name']}
Стартовый капитал: $1000

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/treset — сброс игры
/tleader — таблица лидеров
    """
    
    sent = bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())
    save_message_owner(sent.message_id, user_id)

@bot.message_handler(commands=['tpromo'])
def promo_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
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
            user_data['money'] = round(user_data['money'], 2)
            if 'used_promos' not in user_data:
                user_data['used_promos'] = []
            user_data['used_promos'].append(promo)
            
            promo_data['used_count'] += 1
            save_promocodes(promos)
            save_user(user_id, user_data)
            
            bot.reply_to(message, f"✅ Промокод активирован! +${promo_data['bonus']}")
        else:
            bot.reply_to(message, "❌ Неверный промокод")
            
    except IndexError:
        bot.reply_to(message, "❌ Использование: /tpromo КОД")

@bot.message_handler(commands=['tstats'])
def stats_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
    capital = calculate_total_capital(user_data)
    
    text = f"""
📊 ТВОЯ СТАТИСТИКА (День {user_data['day']})

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
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['tlist'])
def list_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
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
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['tnext'])
def next_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
    change_prices(user_data)
    user_data['day'] += 1
    save_user(user_id, user_data)
    
    text = f"⏩ День {user_data['day']}\n\nЦены обновлены!"
    bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['treset'])
def reset_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
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
    bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['tleader'])
def leaderboard_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    text = get_leaderboard_text()
    bot.send_message(message.chat.id, text, reply_markup=get_main_inline_keyboard())

# ========== ОБРАБОТКА INLINE КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены", show_alert=True)
        return
    
    message_owner = get_message_owner(call.message.message_id)
    
    if message_owner and message_owner != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твои кнопки!", show_alert=True)
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Ошибка загрузки", show_alert=True)
        return
    
    if call.data == "back_to_menu":
        season_data = load_json(SEASON_FILE)
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {user_data['username']}! 👋

Сезон: {season_data['name']}
Стартовый капитал: $1000

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/treset — сброс игры
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_inline_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "status":
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
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "list":
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
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "next":
        change_prices(user_data)
        user_data['day'] += 1
        save_user(user_id, user_data)
        
        text = f"⏩ День {user_data['day']}\n\nЦены обновлены!"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "leaderboard":
        text = get_leaderboard_text()
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "reset":
        username = user_data['username']
        
        new_data = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'companies': DEFAULT_COMPANIES.copy(),
            'prev_prices': {},
            'username': username,
            'first_seen': str(datetime.now()),
            'used_promos': []
        }
        save_user(user_id, new_data)
        
        text = "🔄 Новая игра!\nТы начинаешь заново с $1000"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "promo":
        text = "🎟️ Введи промокод командой /tpromo КОД"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

# ========== ОБРАБОТКА ПОКУПКИ/ПРОДАЖИ ==========
@bot.message_handler(commands=['tbuy'])
def buy_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        success, msg = buy_stock(user_data, ticker, amount)
        
        if success:
            save_user(user_id, user_data)
        
        bot.send_message(message.chat.id, msg, reply_markup=get_main_inline_keyboard())
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Формат: /tbuy AAPL 5", reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['tsell'])
def sell_command(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    user_data = load_user(user_id)
    if not user_data:
        bot.reply_to(message, "❌ Ошибка загрузки")
        return
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        success, msg = sell_stock(user_data, ticker, amount)
        
        if success:
            save_user(user_id, user_data)
        
        bot.send_message(message.chat.id, msg, reply_markup=get_main_inline_keyboard())
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Формат: /tsell AAPL 5", reply_markup=get_main_inline_keyboard())

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

@bot.message_handler(commands=['tadmin'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total_users = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
    leaderboard = load_leaderboard()
    promos = load_promocodes()
    banned = load_banned()
    
    total_promo_uses = sum(p['used_count'] for p in promos.values())
    
    text = f"""
📊 АДМИН СТАТИСТИКА

👥 Всего игроков: {total_users}
🏆 В лидерборде: {len(leaderboard)}
🎟️ Промокодов активировано: {total_promo_uses}
⛔ Забанено: {len(banned)}
    """
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['tban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        banned = load_banned()
        banned[str(user_id)] = True
        save_banned(banned)
        bot.reply_to(message, f"✅ Пользователь {user_id} забанен")
    except:
        bot.reply_to(message, "❌ Использование: /tban ID")

@bot.message_handler(commands=['tunban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        banned = load_banned()
        if str(user_id) in banned:
            del banned[str(user_id)]
            save_banned(banned)
            bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")
        else:
            bot.reply_to(message, "❌ Пользователь не в бане")
    except:
        bot.reply_to(message, "❌ Использование: /tunban ID")

@bot.message_handler(commands=['tgive'])
def give_money(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        
        user_data = load_user(user_id)
        if user_data:
            user_data['money'] += amount
            user_data['money'] = round(user_data['money'], 2)
            save_user(user_id, user_data)
            bot.reply_to(message, f"✅ {amount} выдано пользователю {user_id}")
        else:
            bot.reply_to(message, "❌ Пользователь не найден")
    except:
        bot.reply_to(message, "❌ Использование: /tgive ID СУММА")

@bot.message_handler(commands=['ttake'])
def take_money(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        
        user_data = load_user(user_id)
        if user_data:
            user_data['money'] -= amount
            user_data['money'] = round(user_data['money'], 2)
            save_user(user_id, user_data)
            bot.reply_to(message, f"✅ {amount} забрано у пользователя {user_id}")
        else:
            bot.reply_to(message, "❌ Пользователь не найден")
    except:
        bot.reply_to(message, "❌ Использование: /ttake ID СУММА")

@bot.message_handler(commands=['tresetplayer'])
def reset_player(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        username = f"User_{user_id}"
        
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
        bot.reply_to(message, f"✅ Игрок {user_id} сброшен")
    except:
        bot.reply_to(message, "❌ Использование: /tresetplayer ID")

@bot.message_handler(commands=['taddleader'])
def add_to_leaderboard(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    force_update_leaderboard()
    bot.reply_to(message, "✅ Таблица лидеров принудительно обновлена")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trader с обновленной таблицей лидеров запущен...")
    print(f"🆔 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()