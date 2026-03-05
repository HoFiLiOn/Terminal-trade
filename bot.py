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
TOKEN = "8740420404:AAHli4wJgrgiAKtXeAC7GreL-rtyc2OwMgo"
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ФАЙЛЫ ==========
USERS_DIR = "users"
LEADERBOARD_FILE = "leaderboard.json"
PROMOCODES_FILE = "promocodes.json"
COMPANIES_FILE = "companies.json"

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
    'WMT': {'name': 'Walmart Inc.', 'price': 145.20},
    'NFLX': {'name': 'Netflix Inc.', 'price': 450.30},
    'DIS': {'name': 'Walt Disney Co.', 'price': 110.20},
    'PYPL': {'name': 'PayPal Holdings', 'price': 85.40},
    'ADBE': {'name': 'Adobe Inc.', 'price': 520.10},
    'INTC': {'name': 'Intel Corp.', 'price': 32.80},
    'AMD': {'name': 'AMD Inc.', 'price': 140.60}
}

# ========== ФУНКЦИИ ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_companies():
    companies = load_json(COMPANIES_FILE)
    if not companies:
        companies = DEFAULT_COMPANIES.copy()
        save_json(COMPANIES_FILE, companies)
    return companies

def save_companies(companies):
    save_json(COMPANIES_FILE, companies)

def update_prices():
    companies = load_companies()
    for ticker in companies:
        change = random.uniform(-0.1, 0.1)
        companies[ticker]['price'] = round(companies[ticker]['price'] * (1 + change), 2)
    save_companies(companies)

def get_user_file(user_id):
    return os.path.join(USERS_DIR, f"{user_id}.json")

def get_user(user_id):
    user_file = get_user_file(user_id)
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        user_data = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'username': None
        }
        save_user(user_id, user_data)
        return user_data

def save_user(user_id, data):
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def calculate_capital(user_id):
    user = get_user(user_id)
    companies = load_companies()
    total = user['money']
    for ticker, amount in user['portfolio'].items():
        total += amount * companies[ticker]['price']
    return round(total, 2)

def buy_stock(user_id, ticker, amount):
    companies = load_companies()
    if ticker not in companies:
        return False, "❌ Нет такой компании"
    
    user = get_user(user_id)
    price = companies[ticker]['price']
    total = price * amount
    
    if user['money'] >= total:
        user['money'] -= total
        user['money'] = round(user['money'], 2)
        if ticker in user['portfolio']:
            user['portfolio'][ticker] += amount
        else:
            user['portfolio'][ticker] = amount
        save_user(user_id, user)
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    return False, f"❌ Недостаточно денег. Нужно ${total:,.2f}"

def sell_stock(user_id, ticker, amount):
    companies = load_companies()
    user = get_user(user_id)
    
    if ticker not in user['portfolio']:
        return False, "❌ У вас нет таких акций"
    
    if user['portfolio'][ticker] < amount:
        return False, f"❌ У вас только {user['portfolio'][ticker]} акций"
    
    price = companies[ticker]['price']
    total = price * amount
    
    user['money'] += total
    user['money'] = round(user['money'], 2)
    user['portfolio'][ticker] -= amount
    
    if user['portfolio'][ticker] == 0:
        del user['portfolio'][ticker]
    
    save_user(user_id, user)
    return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"

def get_leaderboard():
    leaderboard = []
    for filename in os.listdir(USERS_DIR):
        user_id = int(filename.replace('.json', ''))
        user = get_user(user_id)
        capital = calculate_capital(user_id)
        username = user.get('username') or f"User_{user_id}"
        leaderboard.append({
            'user_id': user_id,
            'username': username,
            'capital': capital
        })
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    return leaderboard[:10]

# ========== КНОПКИ ==========
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="status"),
        types.InlineKeyboardButton("📈 Компании", callback_data="list"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard")
    )
    return markup

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user = get_user(user_id)
    user['username'] = username
    save_user(user_id, user)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {username}! 👋

💰 Баланс: ${user['money']:,.2f}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tlist — список компаний
/tstats — статистика
/tleader — лидеры
    """
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['tbuy'])
def buy_command(message):
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        success, msg = buy_stock(message.from_user.id, ticker, amount)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "❌ Формат: /tbuy AAPL 5")

@bot.message_handler(commands=['tsell'])
def sell_command(message):
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        success, msg = sell_stock(message.from_user.id, ticker, amount)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "❌ Формат: /tsell AAPL 5")

@bot.message_handler(commands=['tnext'])
def next_command(message):
    update_prices()
    user = get_user(message.from_user.id)
    user['day'] += 1
    save_user(message.from_user.id, user)
    bot.reply_to(message, f"⏩ День {user['day']}! Цены обновлены.")

@bot.message_handler(commands=['tlist'])
def list_command(message):
    companies = load_companies()
    text = "📋 КОМПАНИИ:\n\n"
    for ticker, data in companies.items():
        text += f"{ticker} — {data['name']} — ${data['price']:,.2f}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['tstats'])
def stats_command(message):
    user = get_user(message.from_user.id)
    capital = calculate_capital(message.from_user.id)
    text = f"""
📊 ТВОЯ СТАТИСТИКА
💰 Баланс: ${user['money']:,.2f}
💵 Капитал: ${capital:,.2f}
📅 День: {user['day']}

📋 Портфель:
    """
    if user['portfolio']:
        for ticker, amount in user['portfolio'].items():
            text += f"\n{ticker}: {amount} шт."
    else:
        text += "\nПусто"
    bot.reply_to(message, text)

@bot.message_handler(commands=['tleader'])
def leader_command(message):
    leaderboard = get_leaderboard()
    text = "🏆 ТОП-10:\n\n"
    for i, user in enumerate(leaderboard, 1):
        text += f"{i}. {user['username']} — ${user['capital']:,.2f}\n"
    bot.reply_to(message, text)

# ========== КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "status":
        stats_command(call.message)
    elif call.data == "list":
        list_command(call.message)
    elif call.data == "next":
        next_command(call.message)
    elif call.data == "leaderboard":
        leader_command(call.message)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен...")
    bot.infinity_polling()