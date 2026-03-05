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

# ========== 30 КОМПАНИЙ ==========
DEFAULT_COMPANIES = {
    # Технологические гиганты
    'AAPL': {'name': 'Apple Inc.', 'price': 175.50, 'prev_price': 175.50},
    'MSFT': {'name': 'Microsoft Corp.', 'price': 330.25, 'prev_price': 330.25},
    'GOOG': {'name': 'Alphabet (Google)', 'price': 2800.75, 'prev_price': 2800.75},
    'AMZN': {'name': 'Amazon.com Inc.', 'price': 3450.00, 'prev_price': 3450.00},
    'META': {'name': 'Meta Platforms', 'price': 310.80, 'prev_price': 310.80},
    'NFLX': {'name': 'Netflix Inc.', 'price': 450.30, 'prev_price': 450.30},
    'DIS': {'name': 'Walt Disney Co.', 'price': 110.20, 'prev_price': 110.20},
    'PYPL': {'name': 'PayPal Holdings', 'price': 85.40, 'prev_price': 85.40},
    'ADBE': {'name': 'Adobe Inc.', 'price': 520.10, 'prev_price': 520.10},
    'INTC': {'name': 'Intel Corp.', 'price': 32.80, 'prev_price': 32.80},
    'AMD': {'name': 'AMD Inc.', 'price': 140.60, 'prev_price': 140.60},
    'NVDA': {'name': 'NVIDIA Corp.', 'price': 890.60, 'prev_price': 890.60},
    'CRM': {'name': 'Salesforce Inc.', 'price': 220.30, 'prev_price': 220.30},
    'ORCL': {'name': 'Oracle Corp.', 'price': 115.40, 'prev_price': 115.40},
    'IBM': {'name': 'IBM Corp.', 'price': 145.20, 'prev_price': 145.20},
    
    # Финансовый сектор
    'JPM': {'name': 'JPMorgan Chase', 'price': 150.30, 'prev_price': 150.30},
    'BAC': {'name': 'Bank of America', 'price': 35.20, 'prev_price': 35.20},
    'WFC': {'name': 'Wells Fargo', 'price': 48.50, 'prev_price': 48.50},
    'C': {'name': 'Citigroup Inc.', 'price': 52.30, 'prev_price': 52.30},
    'GS': {'name': 'Goldman Sachs', 'price': 380.40, 'prev_price': 380.40},
    'V': {'name': 'Visa Inc.', 'price': 240.20, 'prev_price': 240.20},
    'MA': {'name': 'Mastercard Inc.', 'price': 390.10, 'prev_price': 390.10},
    
    # Медицина
    'JNJ': {'name': 'Johnson & Johnson', 'price': 160.40, 'prev_price': 160.40},
    'PFE': {'name': 'Pfizer Inc.', 'price': 28.30, 'prev_price': 28.30},
    'MRK': {'name': 'Merck & Co.', 'price': 115.20, 'prev_price': 115.20},
    'ABBV': {'name': 'AbbVie Inc.', 'price': 155.30, 'prev_price': 155.30},
    
    # Ритейл
    'WMT': {'name': 'Walmart Inc.', 'price': 145.20, 'prev_price': 145.20},
    'COST': {'name': 'Costco Wholesale', 'price': 520.30, 'prev_price': 520.30},
    'HD': {'name': 'Home Depot Inc.', 'price': 330.20, 'prev_price': 330.20},
    'MCD': {'name': 'McDonalds Corp.', 'price': 280.40, 'prev_price': 280.40},
    'SBUX': {'name': 'Starbucks Corp.', 'price': 92.30, 'prev_price': 92.30}
}

# ========== ПРОМОКОДЫ ==========
DEFAULT_PROMOCODES = {
    "WELCOME100": {"bonus": 100, "max_uses": 10, "used_count": 0},
    "START500": {"bonus": 500, "max_uses": 10, "used_count": 0},
    "BONUS1000": {"bonus": 1000, "max_uses": 5, "used_count": 0}
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

# ========== КОМПАНИИ ==========
def load_companies():
    companies = load_json(COMPANIES_FILE)
    if not companies:
        companies = DEFAULT_COMPANIES.copy()
        save_json(COMPANIES_FILE, companies)
    return companies

def save_companies(companies):
    save_json(COMPANIES_FILE, companies)

def update_company_prices():
    companies = load_companies()
    
    for ticker, data in companies.items():
        old_price = data['price']
        change = random.uniform(-0.1, 0.1)
        new_price = round(old_price * (1 + change), 2)
        
        data['prev_price'] = old_price
        data['price'] = new_price
    
    save_companies(companies)
    return companies

def get_price_change(old_price, new_price):
    if old_price == 0:
        return "0.00%"
    change = ((new_price - old_price) / old_price) * 100
    return f"{change:+.2f}%"

def get_companies_page(page=1, per_page=10):
    companies = load_companies()
    items = list(companies.items())
    total = len(items)
    
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    
    return page_items, total

# ========== ПОЛЬЗОВАТЕЛИ ==========
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
            'username': None,
            'first_seen': str(datetime.now()),
            'last_seen': str(datetime.now()),
            'used_promos': []
        }
        save_user(user_id, user_data)
        return user_data

def save_user(user_id, data):
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_user_last_seen(user_id):
    user = get_user(user_id)
    user['last_seen'] = str(datetime.now())
    save_user(user_id, user)

def get_portfolio(user_id):
    user = get_user(user_id)
    companies = load_companies()
    portfolio = []
    
    for ticker, amount in user.get('portfolio', {}).items():
        if ticker in companies:
            portfolio.append({
                'ticker': ticker,
                'amount': amount,
                'price': companies[ticker]['price'],
                'name': companies[ticker]['name']
            })
    
    return portfolio

def calculate_capital(user_id):
    user = get_user(user_id)
    companies = load_companies()
    
    total = user['money']
    for ticker, amount in user.get('portfolio', {}).items():
        if ticker in companies:
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
        
        if ticker not in user['portfolio']:
            user['portfolio'][ticker] = 0
        
        user['portfolio'][ticker] += amount
        save_user(user_id, user)
        update_leaderboard()
        
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    else:
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
    update_leaderboard()
    
    return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"

# ========== ЛИДЕРЫ ==========
def update_leaderboard():
    leaderboard = []
    
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = filename.replace('.json', '')
            user = get_user(int(user_id))
            
            capital = calculate_capital(int(user_id))
            username = user.get('username') or f"User_{user_id}"
            
            leaderboard.append({
                'user_id': int(user_id),
                'username': username,
                'capital': capital,
                'day': user['day']
            })
    
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    leaderboard = leaderboard[:50]
    
    save_json(LEADERBOARD_FILE, leaderboard)
    return leaderboard

def get_leaderboard(limit=10):
    leaderboard = load_json(LEADERBOARD_FILE)
    if not leaderboard:
        leaderboard = update_leaderboard()
    return leaderboard[:limit]

def force_update_leaderboard():
    leaderboard = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = filename.replace('.json', '')
            user = get_user(int(user_id))
            capital = calculate_capital(int(user_id))
            username = user.get('username') or f"Player_{user_id}"
            if len(username) > 15:
                username = username[:12] + "..."
            
            leaderboard.append({
                'user_id': int(user_id),
                'username': username,
                'capital': capital,
                'day': user['day']
            })
    
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    leaderboard = leaderboard[:50]
    save_json(LEADERBOARD_FILE, leaderboard)
    return leaderboard

# ========== ПРОМОКОДЫ ==========
def load_promocodes():
    promos = load_json(PROMOCODES_FILE)
    if not promos:
        promos = DEFAULT_PROMOCODES.copy()
        save_json(PROMOCODES_FILE, promos)
    return promos

def save_promocodes(promos):
    save_json(PROMOCODES_FILE, promos)

def get_promocode(code):
    promos = load_promocodes()
    return promos.get(code.upper())

def add_promocode(code, bonus, max_uses):
    promos = load_promocodes()
    code = code.upper()
    
    if code in promos:
        return False
    
    promos[code] = {
        'bonus': bonus,
        'max_uses': max_uses,
        'used_count': 0
    }
    save_promocodes(promos)
    return True

def delete_promocode(code):
    promos = load_promocodes()
    code = code.upper()
    
    if code not in promos:
        return False
    
    del promos[code]
    save_promocodes(promos)
    return True

def use_promo(user_id, promo_code):
    promos = load_promocodes()
    promo_code = promo_code.upper()
    
    if promo_code not in promos:
        return False, "❌ Промокод не найден"
    
    promo = promos[promo_code]
    
    if promo['used_count'] >= promo['max_uses']:
        return False, "❌ Промокод закончился"
    
    user = get_user(user_id)
    
    if promo_code in user.get('used_promos', []):
        return False, "❌ Ты уже активировал этот промокод"
    
    user['money'] += promo['bonus']
    
    if 'used_promos' not in user:
        user['used_promos'] = []
    user['used_promos'].append(promo_code)
    
    save_user(user_id, user)
    
    promo['used_count'] += 1
    save_promocodes(promos)
    
    return True, f"✅ Промокод активирован! +${promo['bonus']}"

# ========== КНОПКИ ==========
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📊 Статус", callback_data="status")
    btn2 = types.InlineKeyboardButton("📈 Компании", callback_data="list")
    btn3 = types.InlineKeyboardButton("⏩ Next", callback_data="next")
    btn4 = types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("◀️ Назад", callback_data="back")
    markup.add(btn)
    return markup

def get_companies_keyboard(current_page, total_pages):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if total_pages > 1:
        btn1 = types.InlineKeyboardButton("◀️", callback_data=f"comp_page_{current_page-1}" if current_page > 1 else "noop")
        btn2 = types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        btn3 = types.InlineKeyboardButton("▶️", callback_data=f"comp_page_{current_page+1}" if current_page < total_pages else "noop")
        markup.add(btn1, btn2, btn3)
    
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="back")
    markup.add(btn_back)
    
    return markup

# ========== КОМАНДЫ ДЛЯ ИГРОКОВ ==========
@bot.message_handler(commands=['trade'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user = get_user(user_id)
    user['username'] = username
    user['last_seen'] = str(datetime.now())
    save_user(user_id, user)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {username}! 👋

💰 Твой баланс: ${user['money']:,.2f}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/tleader — таблица лидеров
    """
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['tbuy'])
def buy_command(message):
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        success, msg = buy_stock(user_id, ticker, amount)
        bot.reply_to(message, msg)
        
        if success:
            update_user_last_seen(user_id)
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Формат: /tbuy AAPL 5")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['tsell'])
def sell_command(message):
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        success, msg = sell_stock(user_id, ticker, amount)
        bot.reply_to(message, msg)
        
        if success:
            update_user_last_seen(user_id)
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Формат: /tsell AAPL 5")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['tnext'])
def next_command(message):
    user_id = message.from_user.id
    
    update_company_prices()
    
    user = get_user(user_id)
    user['day'] += 1
    user['last_seen'] = str(datetime.now())
    save_user(user_id, user)
    
    update_leaderboard()
    
    bot.reply_to(message, "⏩ Новый день! Цены обновлены.", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['tpromo'])
def promo_command(message):
    user_id = message.from_user.id
    
    try:
        promo_code = message.text.split()[1].upper()
        
        promo = get_promocode(promo_code)
        if promo:
            remaining = promo['max_uses'] - promo['used_count']
            text = f"""
🎟️ Промокод: {promo_code}
💰 Бонус: +${promo['bonus']}
🎫 Доступно: {remaining}/{promo['max_uses']}
            """
            bot.reply_to(message, text)
            
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("✅ Активировать", callback_data=f"confirm_promo_{promo_code}")
            btn2 = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_promo")
            markup.add(btn1, btn2)
            
            bot.send_message(message.chat.id, "Активировать промокод?", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ Промокод не найден")
            
    except IndexError:
        bot.reply_to(message, "❌ Использование: /tpromo КОД")

@bot.message_handler(commands=['tlist'])
def list_command(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    companies, total = get_companies_page(page=1)
    total_pages = (total + 9) // 10
    
    text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
    
    for ticker, data in companies:
        change = get_price_change(data.get('prev_price', data['price']), data['price'])
        
        if change.startswith('+'):
            emoji = "🟢"
        elif change.startswith('-'):
            emoji = "🔴"
        else:
            emoji = "⚪"
        
        text += f"{ticker} — {data['name']}\n"
        text += f"💰 ${data['price']:,.2f} {emoji} {change}\n\n"
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=get_companies_keyboard(1, total_pages)
    )

@bot.message_handler(commands=['tstats'])
def stats_command(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    capital = calculate_capital(user_id)
    portfolio = get_portfolio(user_id)
    
    text = f"""
📊 ТВОЯ СТАТИСТИКА (День {user['day']})

💰 Баланс: ${user['money']:,.2f}
💵 Капитал: ${capital:,.2f}

📋 Портфель:
    """
    
    if portfolio:
        for p in portfolio:
            value = p['amount'] * p['price']
            text += f"\n{p['ticker']}: {p['amount']} шт. (${value:,.2f})"
    else:
        text += "\nУ вас пока нет акций"
    
    leaderboard = get_leaderboard(50)
    for i, entry in enumerate(leaderboard, 1):
        if entry['user_id'] == user_id:
            text += f"\n\n⭐ Место: {i} из {len(leaderboard)}"
            break
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['tleader'])
def leaderboard_command(message):
    leaderboard = get_leaderboard(10)
    
    text = f"🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
    
    for i, entry in enumerate(leaderboard, 1):
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        name = entry['username'][:15] + "..." if len(entry['username']) > 15 else entry['username']
        text += f"{medal} {name} — ${entry['capital']:,.2f}\n"
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "back":
        user = get_user(user_id)
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/tleader — таблица лидеров
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "status":
        user = get_user(user_id)
        capital = calculate_capital(user_id)
        portfolio = get_portfolio(user_id)
        
        text = f"""
📊 ТВОЙ СТАТУС (День {user['day']})

💰 Баланс: ${user['money']:,.2f}
💵 Капитал: ${capital:,.2f}

📋 Портфель:
        """
        
        if portfolio:
            for p in portfolio:
                value = p['amount'] * p['price']
                text += f"\n{p['ticker']}: {p['amount']} шт. (${value:,.2f})"
        else:
            text += "\nУ вас пока нет акций"
        
        leaderboard = get_leaderboard(50)
        for i, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user_id:
                text += f"\n\n⭐ Место: {i} из {len(leaderboard)}"
                break
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "list":
        user = get_user(user_id)
        companies, total = get_companies_page(page=1)
        total_pages = (total + 9) // 10
        
        text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
        
        for ticker, data in companies:
            change = get_price_change(data.get('prev_price', data['price']), data['price'])
            
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
            reply_markup=get_companies_keyboard(1, total_pages)
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("comp_page_"):
        if call.data == "comp_page_noop":
            bot.answer_callback_query(call.id)
            return
        
        page = int(call.data.split("_")[2])
        user = get_user(user_id)
        companies, total = get_companies_page(page=page)
        total_pages = (total + 9) // 10
        
        text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
        
        for ticker, data in companies:
            change = get_price_change(data.get('prev_price', data['price']), data['price'])
            
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
            reply_markup=get_companies_keyboard(page, total_pages)
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "next":
        update_company_prices()
        user = get_user(user_id)
        user['day'] += 1
        user['last_seen'] = str(datetime.now())
        save_user(user_id, user)
        update_leaderboard()
        
        bot.edit_message_text(
            "⏩ Новый день! Цены обновлены.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "leaderboard":
        leaderboard = get_leaderboard(10)
        
        text = f"🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
        
        for i, entry in enumerate(leaderboard, 1):
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            name = entry['username'][:15] + "..." if len(entry['username']) > 15 else entry['username']
            text += f"{medal} {name} — ${entry['capital']:,.2f}\n"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("confirm_promo_"):
        promo_code = call.data.replace("confirm_promo_", "")
        
        success, msg = use_promo(user_id, promo_code)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        
        if success:
            update_user_last_seen(user_id)
            update_leaderboard()
        
        user = get_user(user_id)
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/tleader — таблица лидеров
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    elif call.data == "cancel_promo":
        bot.answer_callback_query(call.id, "Отменено")
        user = get_user(user_id)
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
/tlist — список компаний
/tstats — статистика
/tleader — таблица лидеров
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
    
    elif call.data == "noop":
        bot.answer_callback_query(call.id)

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['admin'])
def admin_help(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Недостаточно прав")
        return
    
    text = """
👑 **АДМИН-КОМАНДЫ**

**Управление игроками:**
/admin give ID СУММА — выдать деньги
/admin take ID СУММА — забрать деньги
/admin reset ID — сбросить игрока

**Управление промокодами:**
/admin promo add КОД БОНУС МАКС — добавить
/admin promo del КОД — удалить
/admin promos — список промокодов

**Управление компаниями:**
/admin comps — список компаний
/admin comp add ТИКЕР НАЗВАНИЕ ЦЕНА — добавить
/admin comp del ТИКЕР — удалить

**Статистика:**
/admin stats — общая статистика
/admin top — топ-10
    """
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'give'])
def admin_give(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[2])
        amount = float(parts[3])
        
        user = get_user(target_id)
        user['money'] += amount
        user['money'] = round(user['money'], 2)
        save_user(target_id, user)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ Пользователю {target_id} выдано ${amount:,.2f}")
    except:
        bot.reply_to(message, "❌ Использование: /admin give ID СУММА")

@bot.message_handler(commands=['admin', 'take'])
def admin_take(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[2])
        amount = float(parts[3])
        
        user = get_user(target_id)
        user['money'] -= amount
        user['money'] = round(user['money'], 2)
        save_user(target_id, user)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ У пользователя {target_id} забрано ${amount:,.2f}")
    except:
        bot.reply_to(message, "❌ Использование: /admin take ID СУММА")

@bot.message_handler(commands=['admin', 'reset'])
def admin_reset(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[2])
        
        user_data = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'username': None,
            'first_seen': str(datetime.now()),
            'last_seen': str(datetime.now()),
            'used_promos': []
        }
        save_user(target_id, user_data)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ Пользователь {target_id} сброшен")
    except:
        bot.reply_to(message, "❌ Использование: /admin reset ID")

@bot.message_handler(commands=['admin', 'promo', 'add'])
def admin_promo_add(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        code = parts[3].upper()
        bonus = int(parts[4])
        max_uses = int(parts[5])
        
        success = add_promocode(code, bonus, max_uses)
        
        if success:
            bot.reply_to(message, f"✅ Промокод {code} добавлен (${bonus}, {max_uses} использований)")
        else:
            bot.reply_to(message, "❌ Промокод уже существует")
    except:
        bot.reply_to(message, "❌ Использование: /admin promo add КОД БОНУС МАКС")

@bot.message_handler(commands=['admin', 'promo', 'del'])
def admin_promo_del(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        code = message.text.split()[3].upper()
        
        success = delete_promocode(code)
        
        if success:
            bot.reply_to(message, f"✅ Промокод {code} удален")
        else:
            bot.reply_to(message, "❌ Промокод не найден")
    except:
        bot.reply_to(message, "❌ Использование: /admin promo del КОД")

@bot.message_handler(commands=['admin', 'promos'])
def admin_promos(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    promos = load_promocodes()
    
    if not promos:
        bot.reply_to(message, "📋 Нет промокодов")
        return
    
    text = "🎟️ **ВСЕ ПРОМОКОДЫ**\n\n"
    for code, data in promos.items():
        remaining = data['max_uses'] - data['used_count']
        text += f"{code} — ${data['bonus']} — {data['used_count']}/{data['max_uses']} (осталось {remaining})\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'comps'])
def admin_comps(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    companies = load_companies()
    
    text = "📋 **ВСЕ КОМПАНИИ**\n\n"
    for ticker, data in companies.items():
        text += f"{ticker} — {data['name']} — ${data['price']:,.2f}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'comp', 'add'])
def admin_comp_add(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[3].upper()
        name = ' '.join(parts[4:-1])
        price = float(parts[-1])
        
        companies = load_companies()
        companies[ticker] = {
            'name': name,
            'price': price,
            'prev_price': price
        }
        save_companies(companies)
        
        bot.reply_to(message, f"✅ Компания {ticker} добавлена")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp add ТИКЕР НАЗВАНИЕ ЦЕНА")

@bot.message_handler(commands=['admin', 'comp', 'del'])
def admin_comp_del(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        ticker = message.text.split()[3].upper()
        
        companies = load_companies()
        if ticker in companies:
            del companies[ticker]
            save_companies(companies)
            bot.reply_to(message, f"✅ Компания {ticker} удалена")
        else:
            bot.reply_to(message, "❌ Компания не найдена")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp del ТИКЕР")

@bot.message_handler(commands=['admin', 'stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total_users = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
    total_money = 0
    
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = filename.replace('.json', '')
            user = get_user(int(user_id))
            total_money += user['money']
    
    promos = load_promocodes()
    total_promos = len(promos)
    total_activations = sum(p['used_count'] for p in promos.values())
    
    companies = load_companies()
    total_companies = len(companies)
    
    text = f"""
📊 **ОБЩАЯ СТАТИСТИКА**

👥 Всего игроков: {total_users}
💰 Всего денег: ${total_money:,.2f}
🎟️ Промокодов: {total_promos}
🎫 Активаций: {total_activations}
🏢 Компаний: {total_companies}
    """
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'top'])
def admin_top(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    leaderboard = get_leaderboard(10)
    
    text = "🏆 **ТОП-10 ПО КАПИТАЛУ**\n\n"
    
    for i, entry in enumerate(leaderboard, 1):
        text += f"{i}. {entry['username']} — ${entry['capital']:,.2f}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade (30 КОМПАНИЙ) запущен...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()