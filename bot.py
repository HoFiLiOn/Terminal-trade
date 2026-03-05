import telebot
from telebot import types
import random
import sqlite3
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

# ========== ПОДКЛЮЧЕНИЕ К БД ==========
def get_db():
    conn = sqlite3.connect('terminal_trade.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            money REAL DEFAULT 1000,
            day INTEGER DEFAULT 1,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            used_promos TEXT DEFAULT '[]',
            warns INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица портфеля
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            user_id INTEGER,
            ticker TEXT,
            amount INTEGER,
            buy_price REAL,
            PRIMARY KEY (user_id, ticker)
        )
    ''')
    
    # Таблица компаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            prev_price REAL,
            volatility REAL DEFAULT 0.1
        )
    ''')
    
    # Таблица лидеров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            capital REAL,
            day INTEGER,
            last_update TIMESTAMP
        )
    ''')
    
    # Таблица промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            bonus INTEGER,
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица сезонов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Таблица логов админа
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Заполняем компании если пусто (10 компаний)
    cursor.execute('SELECT COUNT(*) FROM companies')
    if cursor.fetchone()[0] == 0:
        companies = [
            ('AAPL', 'Apple Inc.', 175.50, 175.50, 0.1),
            ('MSFT', 'Microsoft Corp.', 330.25, 330.25, 0.1),
            ('GOOG', 'Alphabet (Google)', 2800.75, 2800.75, 0.1),
            ('AMZN', 'Amazon.com Inc.', 3450.00, 3450.00, 0.1),
            ('TSLA', 'Tesla Inc.', 900.50, 900.50, 0.15),
            ('META', 'Meta Platforms', 310.80, 310.80, 0.12),
            ('NVDA', 'NVIDIA Corp.', 890.60, 890.60, 0.15),
            ('JPM', 'JPMorgan Chase', 150.30, 150.30, 0.08),
            ('JNJ', 'Johnson & Johnson', 160.40, 160.40, 0.07),
            ('WMT', 'Walmart Inc.', 145.20, 145.20, 0.07)
        ]
        cursor.executemany('INSERT INTO companies VALUES (?,?,?,?,?)', companies)
    
    conn.commit()
    conn.close()

init_db()

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Terminal Trade is alive!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ========== ФУНКЦИИ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        now = datetime.now()
        cursor.execute('''
            INSERT INTO users (user_id, first_seen, last_seen)
            VALUES (?, ?, ?)
        ''', (user_id, now, now))
        conn.commit()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    values.append(user_id)
    cursor.execute(f'''
        UPDATE users 
        SET {', '.join(fields)}, last_seen = ?
        WHERE user_id = ?
    ''', (*values, datetime.now(), user_id))
    
    conn.commit()
    conn.close()

def add_coins(user_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def take_coins(user_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET money = money - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ========== ФУНКЦИИ ДЛЯ КОМПАНИЙ ==========
def get_companies(page=1, per_page=10):
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    cursor.execute('''
        SELECT * FROM companies 
        ORDER BY ticker 
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    companies = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM companies')
    total = cursor.fetchone()[0]
    
    conn.close()
    return companies, total

def update_company_prices():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT ticker, price, volatility FROM companies')
    companies = cursor.fetchall()
    
    for ticker, old_price, vol in companies:
        change = random.uniform(-vol, vol)
        new_price = round(old_price * (1 + change), 2)
        
        cursor.execute('''
            UPDATE companies 
            SET price = ?, prev_price = ?
            WHERE ticker = ?
        ''', (new_price, old_price, ticker))
    
    conn.commit()
    conn.close()

def get_price_change(old_price, new_price):
    if old_price == 0:
        return "0.00%"
    change = ((new_price - old_price) / old_price) * 100
    return f"{change:+.2f}%"

def add_company(ticker, name, price, volatility=0.1):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO companies (ticker, name, price, prev_price, volatility)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticker.upper(), name, price, price, volatility))
        conn.commit()
        success = True
    except:
        success = False
    
    conn.close()
    return success

def delete_company(ticker):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM companies WHERE ticker = ?', (ticker.upper(),))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0

def set_company_price(ticker, price):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT price FROM companies WHERE ticker = ?', (ticker.upper(),))
    company = cursor.fetchone()
    
    if not company:
        conn.close()
        return False
    
    cursor.execute('''
        UPDATE companies 
        SET price = ?, prev_price = price
        WHERE ticker = ?
    ''', (price, ticker.upper()))
    
    conn.commit()
    conn.close()
    return True

# ========== ФУНКЦИИ ДЛЯ ИГРОКОВ ==========
def get_portfolio(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, c.price, c.name 
        FROM portfolio p
        JOIN companies c ON p.ticker = c.ticker
        WHERE p.user_id = ?
    ''', (user_id,))
    
    portfolio = cursor.fetchall()
    conn.close()
    return portfolio

def calculate_capital(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT money FROM users WHERE user_id = ?', (user_id,))
    money = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT SUM(p.amount * c.price) 
        FROM portfolio p
        JOIN companies c ON p.ticker = c.ticker
        WHERE p.user_id = ?
    ''', (user_id,))
    
    stocks = cursor.fetchone()[0] or 0
    conn.close()
    
    return round(money + stocks, 2)

def buy_stock(user_id, ticker, amount):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT price FROM companies WHERE ticker = ?', (ticker,))
    company = cursor.fetchone()
    
    if not company:
        conn.close()
        return False, "❌ Нет такой компании"
    
    price = company[0]
    total = price * amount
    
    cursor.execute('SELECT money FROM users WHERE user_id = ?', (user_id,))
    money = cursor.fetchone()[0]
    
    if money >= total:
        new_money = round(money - total, 2)
        cursor.execute('UPDATE users SET money = ? WHERE user_id = ?', (new_money, user_id))
        
        cursor.execute('''
            INSERT INTO portfolio (user_id, ticker, amount, buy_price)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) 
            DO UPDATE SET amount = amount + excluded.amount
        ''', (user_id, ticker, amount, price))
        
        conn.commit()
        conn.close()
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    else:
        conn.close()
        return False, f"❌ Недостаточно денег. Нужно ${total:,.2f}"

def sell_stock(user_id, ticker, amount):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT amount FROM portfolio 
        WHERE user_id = ? AND ticker = ?
    ''', (user_id, ticker))
    portfolio = cursor.fetchone()
    
    if not portfolio or portfolio[0] < amount:
        conn.close()
        return False, f"❌ У вас только {portfolio[0] if portfolio else 0} акций {ticker}"
    
    cursor.execute('SELECT price FROM companies WHERE ticker = ?', (ticker,))
    price = cursor.fetchone()[0]
    total = price * amount
    
    cursor.execute('SELECT money FROM users WHERE user_id = ?', (user_id,))
    money = cursor.fetchone()[0]
    new_money = round(money + total, 2)
    cursor.execute('UPDATE users SET money = ? WHERE user_id = ?', (new_money, user_id))
    
    if portfolio[0] == amount:
        cursor.execute('DELETE FROM portfolio WHERE user_id = ? AND ticker = ?', (user_id, ticker))
    else:
        cursor.execute('''
            UPDATE portfolio 
            SET amount = amount - ? 
            WHERE user_id = ? AND ticker = ?
        ''', (amount, user_id, ticker))
    
    conn.commit()
    conn.close()
    
    return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"

# ========== ФУНКЦИИ ДЛЯ ЛИДЕРОВ ==========
def update_leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM leaderboard')
    
    cursor.execute('SELECT user_id, username FROM users WHERE banned = 0')
    users = cursor.fetchall()
    
    for user in users:
        user_id = user[0]
        username = user[1] or f"User_{user_id}"
        capital = calculate_capital(user_id)
        
        cursor.execute('''
            INSERT INTO leaderboard (user_id, username, capital, last_update)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, capital, datetime.now()))
    
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, capital 
        FROM leaderboard 
        ORDER BY capital DESC 
        LIMIT ?
    ''', (limit,))
    
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

# ========== ФУНКЦИИ ДЛЯ ПРОМОКОДОВ ==========
def get_promocode(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM promocodes WHERE code = ?', (code.upper(),))
    promo = cursor.fetchone()
    conn.close()
    return promo

def add_promocode(code, bonus, max_uses):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO promocodes (code, bonus, max_uses)
            VALUES (?, ?, ?)
        ''', (code.upper(), bonus, max_uses))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success

def delete_promocode(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM promocodes WHERE code = ?', (code.upper(),))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def use_promo(user_id, promo_code, username):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM promocodes WHERE code = ?', (promo_code.upper(),))
    promo = cursor.fetchone()
    
    if not promo:
        conn.close()
        return False, "❌ Промокод не найден"
    
    if promo['used_count'] >= promo['max_uses']:
        conn.close()
        return False, "❌ Промокод закончился"
    
    cursor.execute('SELECT used_promos FROM users WHERE user_id = ?', (user_id,))
    used = eval(cursor.fetchone()[0])
    
    if promo_code.upper() in used:
        conn.close()
        return False, "❌ Ты уже активировал этот промокод"
    
    # Начисляем бонус
    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?', (promo['bonus'], user_id))
    
    # Обновляем список использованных
    used.append(promo_code.upper())
    cursor.execute('UPDATE users SET used_promos = ? WHERE user_id = ?', (str(used), user_id))
    
    # Обновляем счетчик
    cursor.execute('UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?', (promo_code.upper(),))
    
    conn.commit()
    conn.close()
    
    return True, f"✅ Промокод активирован! +${promo['bonus']}"

# ========== ФУНКЦИИ ДЛЯ СЕЗОНОВ ==========
def get_current_season():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM seasons WHERE active = 1 ORDER BY id DESC LIMIT 1')
    season = cursor.fetchone()
    conn.close()
    return season

def create_season(name, days):
    conn = get_db()
    cursor = conn.cursor()
    start = datetime.now()
    end = start + timedelta(days=days)
    
    # Деактивируем все старые сезоны
    cursor.execute('UPDATE seasons SET active = 0')
    
    cursor.execute('''
        INSERT INTO seasons (name, start_date, end_date, active)
        VALUES (?, ?, ?, 1)
    ''', (name, start, end))
    
    conn.commit()
    conn.close()
    return True

def end_season():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE seasons SET active = 0')
    conn.commit()
    conn.close()

def get_season_time_left():
    season = get_current_season()
    if not season:
        return None, None
    
    end = datetime.fromisoformat(season['end_date'])
    now = datetime.now()
    
    if now > end:
        return None, None
    
    days = (end - now).days
    hours = ((end - now).seconds // 3600)
    return days, hours

# ========== ФУНКЦИИ ДЛЯ РАССЫЛОК ==========
def broadcast_to_all(text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            bot.send_message(user[0], f"📢 **РАССЫЛКА**\n\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            failed += 1
    
    return sent, failed

def broadcast_to_active(text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE last_seen > ?', (datetime.now() - timedelta(days=7),))
    users = cursor.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            bot.send_message(user[0], f"📢 **РАССЫЛКА**\n\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            failed += 1
    
    return sent, failed

# ========== КНОПКИ ==========
def get_main_keyboard():
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
    btn = types.InlineKeyboardButton("◀️ Назад", callback_data="back")
    markup.add(btn)
    return markup

def get_companies_keyboard(current_page, total_pages):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if total_pages > 1:
        btn1 = types.InlineKeyboardButton("◀️", callback_data=f"comp_page_{current_page-1}")
        btn2 = types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        btn3 = types.InlineKeyboardButton("▶️", callback_data=f"comp_page_{current_page+1}")
        markup.add(btn1, btn2, btn3)
    
    return markup

# ========== КОМАНДЫ ДЛЯ ИГРОКОВ ==========
@bot.message_handler(commands=['trade'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user = get_user(user_id)
    update_user(user_id, username=username)
    
    season = get_current_season()
    season_name = season['name'] if season else "ВЕСНА"
    days_left, hours_left = get_season_time_left()
    
    time_left = ""
    if days_left is not None:
        time_left = f"\nДо конца сезона: {days_left}д {hours_left}ч"
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

Привет, {username}! 👋

💰 Стартовый капитал: $1000
{time_left}

Команды:
/tbuy AAPL 5 — купить
/tsell TSLA 2 — продать
/tnext — следующий день
/tpromo КОД — промокод
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
            update_leaderboard()
        
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
            update_leaderboard()
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Формат: /tsell AAPL 5")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['tnext'])
def next_command(message):
    update_company_prices()
    update_leaderboard()
    bot.reply_to(message, "⏩ Новый день! Цены обновлены.")

@bot.message_handler(commands=['tpromo'])
def promo_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
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
            
            # Спрашиваем подтверждение
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
    companies, total = get_companies(page=1)
    total_pages = (total + 9) // 10
    
    text = f"📋 КОМПАНИИ (1/{total_pages})\n\n"
    
    for c in companies:
        ticker, name, price, prev = c[0], c[1], c[2], c[3]
        change = get_price_change(prev, price)
        
        if change.startswith('+'):
            emoji = "🟢"
        elif change.startswith('-'):
            emoji = "🔴"
        else:
            emoji = "⚪"
        
        text += f"{ticker} — {name[:15]} — ${price:,.2f} {emoji} {change}\n"
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=get_companies_keyboard(1, total_pages)
    )

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "back":
        user = get_user(user_id)
        season = get_current_season()
        season_name = season['name'] if season else "ВЕСНА"
        days_left, hours_left = get_season_time_left()
        
        time_left = ""
        if days_left is not None:
            time_left = f"\nДо конца сезона: {days_left}д {hours_left}ч"
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}
{time_left}
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
        money = user[2]
        day = user[3]
        capital = calculate_capital(user_id)
        portfolio = get_portfolio(user_id)
        
        text = f"""
📊 ТВОЙ СТАТУС (День {day})

💰 Баланс: ${money:,.2f}
💵 Капитал: ${capital:,.2f}

📋 Портфель:
        """
        
        if portfolio:
            for p in portfolio:
                ticker = p[1]
                amount = p[2]
                current_price = p[4]
                value = amount * current_price
                text += f"\n{ticker}: {amount} шт. (${value:,.2f})"
        else:
            text += "\nУ вас пока нет акций"
        
        leaderboard = get_leaderboard(50)
        for i, entry in enumerate(leaderboard, 1):
            if entry[0] == user_id:
                text += f"\n\n⭐ Место: {i} из {len(leaderboard)}"
                break
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("comp_page_"):
        page = int(call.data.split("_")[2])
        companies, total = get_companies(page=page)
        total_pages = (total + 9) // 10
        
        text = f"📋 КОМПАНИИ ({page}/{total_pages})\n\n"
        
        for c in companies:
            ticker, name, price, prev = c[0], c[1], c[2], c[3]
            change = get_price_change(prev, price)
            
            if change.startswith('+'):
                emoji = "🟢"
            elif change.startswith('-'):
                emoji = "🔴"
            else:
                emoji = "⚪"
            
            text += f"{ticker} — {name[:15]} — ${price:,.2f} {emoji} {change}\n"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_companies_keyboard(page, total_pages)
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "next":
        update_company_prices()
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
            user_id_lb, username, capital = entry
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            name = username[:15] + "..." if len(username) > 15 else username
            text += f"{medal} {name} — ${capital:,.2f}\n"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "reset":
        update_user(user_id, money=1000, day=1)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM portfolio WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        update_leaderboard()
        
        bot.edit_message_text(
            "🔄 Новая игра! Ты начинаешь заново с $1000",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "promo":
        bot.edit_message_text(
            "🎟️ Введи промокод командой /tpromo КОД",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("confirm_promo_"):
        promo_code = call.data.replace("confirm_promo_", "")
        username = call.from_user.username or call.from_user.first_name
        
        success, msg = use_promo(user_id, promo_code, username)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        
        if success:
            update_leaderboard()
        
        user = get_user(user_id)
        season = get_current_season()
        season_name = season['name'] if season else "ВЕСНА"
        days_left, hours_left = get_season_time_left()
        
        time_left = ""
        if days_left is not None:
            time_left = f"\nДо конца сезона: {days_left}д {hours_left}ч"
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}
{time_left}
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
        season = get_current_season()
        season_name = season['name'] if season else "ВЕСНА"
        days_left, hours_left = get_season_time_left()
        
        time_left = ""
        if days_left is not None:
            time_left = f"\nДо конца сезона: {days_left}д {hours_left}ч"
        
        text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
╚══════════════════════════════╝

💰 Твой баланс: ${user['money']:,.2f}
{time_left}
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['admin'])
def admin_help(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = """
👑 **АДМИН-КОМАНДЫ**

**Управление игроками:**
/admin give ID СУММА — выдать деньги
/admin take ID СУММА — забрать деньги
/admin ban ID — забанить
/admin unban ID — разбанить
/admin reset ID — сбросить игрока

**Управление компаниями:**
/admin comps — список компаний
/admin comp add ТИКЕР НАЗВАНИЕ ЦЕНА — добавить
/admin comp del ТИКЕР — удалить
/admin comp price ТИКЕР ЦЕНА — изменить цену
/admin comp vol ТИКЕР 0.1 — изменить волатильность

**Управление промокодами:**
/admin promo add КОД БОНУС МАКС — добавить
/admin promo del КОД — удалить
/admin promos — список промокодов

**Управление сезонами:**
/admin season create НАЗВАНИЕ ДНЕЙ — создать сезон
/admin season end — завершить сезон
/admin season — текущий сезон

**Рассылки:**
/admin broadcast ТЕКСТ — всем игрокам
/admin broadcast active ТЕКСТ — активным за 7 дней

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
        
        add_coins(target_id, amount)
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
        
        take_coins(target_id, amount)
        bot.reply_to(message, f"✅ У пользователя {target_id} забрано ${amount:,.2f}")
    except:
        bot.reply_to(message, "❌ Использование: /admin take ID СУММА")

@bot.message_handler(commands=['admin', 'ban'])
def admin_ban(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[2])
        ban_user(target_id)
        bot.reply_to(message, f"✅ Пользователь {target_id} забанен")
    except:
        bot.reply_to(message, "❌ Использование: /admin ban ID")

@bot.message_handler(commands=['admin', 'unban'])
def admin_unban(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[2])
        unban_user(target_id)
        bot.reply_to(message, f"✅ Пользователь {target_id} разбанен")
    except:
        bot.reply_to(message, "❌ Использование: /admin unban ID")

@bot.message_handler(commands=['admin', 'reset'])
def admin_reset(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[2])
        
        update_user(target_id, money=1000, day=1)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM portfolio WHERE user_id = ?', (target_id,))
        conn.commit()
        conn.close()
        
        update_leaderboard()
        
        bot.reply_to(message, f"✅ Пользователь {target_id} сброшен")
    except:
        bot.reply_to(message, "❌ Использование: /admin reset ID")

@bot.message_handler(commands=['admin', 'comps'])
def admin_comps(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    companies, total = get_companies(page=1, per_page=100)
    
    text = "📋 **ВСЕ КОМПАНИИ**\n\n"
    for c in companies:
        text += f"{c[0]} — {c[1]} — ${c[2]:,.2f} (vol: {c[4]})\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'comp', 'add'])
def admin_comp_add(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[3].upper()
        name = parts[4]
        price = float(parts[5])
        vol = float(parts[6]) if len(parts) > 6 else 0.1
        
        success = add_company(ticker, name, price, vol)
        
        if success:
            bot.reply_to(message, f"✅ Компания {ticker} добавлена")
        else:
            bot.reply_to(message, "❌ Ошибка добавления (возможно тикер уже существует)")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp add ТИКЕР НАЗВАНИЕ ЦЕНА [ВОЛАТИЛЬНОСТЬ]")

@bot.message_handler(commands=['admin', 'comp', 'del'])
def admin_comp_del(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        ticker = message.text.split()[3].upper()
        
        success = delete_company(ticker)
        
        if success:
            bot.reply_to(message, f"✅ Компания {ticker} удалена")
        else:
            bot.reply_to(message, "❌ Компания не найдена")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp del ТИКЕР")

@bot.message_handler(commands=['admin', 'comp', 'price'])
def admin_comp_price(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[3].upper()
        price = float(parts[4])
        
        success = set_company_price(ticker, price)
        
        if success:
            bot.reply_to(message, f"✅ Цена {ticker} изменена на ${price:,.2f}")
        else:
            bot.reply_to(message, "❌ Компания не найдена")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp price ТИКЕР ЦЕНА")

@bot.message_handler(commands=['admin', 'comp', 'vol'])
def admin_comp_vol(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[3].upper()
        vol = float(parts[4])
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE companies SET volatility = ? WHERE ticker = ?', (vol, ticker))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ Волатильность {ticker} изменена на {vol}")
    except:
        bot.reply_to(message, "❌ Использование: /admin comp vol ТИКЕР 0.1")

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
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM promocodes ORDER BY used_count DESC')
    promos = cursor.fetchall()
    conn.close()
    
    if not promos:
        bot.reply_to(message, "📋 Нет промокодов")
        return
    
    text = "🎟️ **ВСЕ ПРОМОКОДЫ**\n\n"
    for p in promos:
        remaining = p['max_uses'] - p['used_count']
        text += f"{p['code']} — ${p['bonus']} — {p['used_count']}/{p['max_uses']} (осталось {remaining})\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'season', 'create'])
def admin_season_create(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        name = parts[3]
        days = int(parts[4])
        
        create_season(name, days)
        bot.reply_to(message, f"✅ Сезон '{name}' создан на {days} дней")
    except:
        bot.reply_to(message, "❌ Использование: /admin season create НАЗВАНИЕ ДНЕЙ")

@bot.message_handler(commands=['admin', 'season', 'end'])
def admin_season_end(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    end_season()
    bot.reply_to(message, "✅ Текущий сезон завершен")

@bot.message_handler(commands=['admin', 'season'])
def admin_season(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    season = get_current_season()
    
    if not season:
        bot.reply_to(message, "📋 Нет активного сезона")
        return
    
    days_left, hours_left = get_season_time_left()
    
    text = f"""
📋 **ТЕКУЩИЙ СЕЗОН**

Название: {season['name']}
Начало: {season['start_date'][:10]}
Конец: {season['end_date'][:10]}
Осталось: {days_left}д {hours_left}ч
    """
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin', 'broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        text = message.text.replace('/admin broadcast', '').strip()
        
        if not text:
            bot.reply_to(message, "❌ Введи текст рассылки")
            return
        
        sent, failed = broadcast_to_all(text)
        bot.reply_to(message, f"✅ Рассылка завершена\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")
    except:
        bot.reply_to(message, "❌ Использование: /admin broadcast ТЕКСТ")

@bot.message_handler(commands=['admin', 'broadcast', 'active'])
def admin_broadcast_active(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        text = message.text.replace('/admin broadcast active', '').strip()
        
        if not text:
            bot.reply_to(message, "❌ Введи текст рассылки")
            return
        
        sent, failed = broadcast_to_active(text)
        bot.reply_to(message, f"✅ Рассылка активным завершена\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")
    except:
        bot.reply_to(message, "❌ Использование: /admin broadcast active ТЕКСТ")

@bot.message_handler(commands=['admin', 'stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1')
    banned_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(money) FROM users')
    total_money = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM promocodes')
    total_promos = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(used_count) FROM promocodes')
    total_activations = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM companies')
    total_companies = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"""
📊 **ОБЩАЯ СТАТИСТИКА**

👥 Всего игроков: {total_users}
⛔ Забанено: {banned_users}
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
        user_id, username, capital = entry
        text += f"{i}. {username} — ${capital:,.2f}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade с админкой запущен...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()