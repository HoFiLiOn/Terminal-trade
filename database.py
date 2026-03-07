import sqlite3
import os
from datetime import datetime, timedelta
from config import DB_PATH

def get_db():
    """Получить соединение с БД"""
    # Создаем папку data если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Создать все таблицы при первом запуске"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            money REAL DEFAULT 1000.0,
            day INTEGER DEFAULT 1,
            cubes INTEGER DEFAULT 0,
            shields INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица портфеля (акции пользователей)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            user_id INTEGER,
            ticker TEXT,
            amount INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, ticker),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица инвентаря
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id TEXT,
            name TEXT,
            emoji TEXT,
            description TEXT,
            category TEXT,
            effect TEXT,
            acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица активных эффектов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_effects (
            user_id INTEGER PRIMARY KEY,
            booster_end TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица подписок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sub_type TEXT,
            bonus INTEGER,
            end_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица использованных промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_promos (
            user_id INTEGER,
            promo_code TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, promo_code),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица компаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            prev_price REAL
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
    
    # Таблица сезона (только одна запись)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    
    # Заполняем начальными данными
    init_default_data(cursor)
    
    conn.commit()
    conn.close()
    
    print("✅ База данных создана!")

def init_default_data(cursor):
    """Заполнить таблицы начальными данными"""
    
    # Проверяем компании
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        companies = [
            ('AAPL', 'Apple Inc.', 175.50, 175.50),
            ('MSFT', 'Microsoft Corp.', 330.25, 330.25),
            ('GOOG', 'Alphabet (Google)', 2800.75, 2800.75),
            ('AMZN', 'Amazon.com Inc.', 3450.00, 3450.00),
            ('META', 'Meta Platforms', 310.80, 310.80),
            ('NFLX', 'Netflix Inc.', 450.30, 450.30),
            ('DIS', 'Walt Disney Co.', 110.20, 110.20),
            ('PYPL', 'PayPal Holdings', 85.40, 85.40),
            ('ADBE', 'Adobe Inc.', 520.10, 520.10),
            ('INTC', 'Intel Corp.', 32.80, 32.80),
            ('AMD', 'AMD Inc.', 140.60, 140.60),
            ('NVDA', 'NVIDIA Corp.', 890.60, 890.60),
            ('CRM', 'Salesforce Inc.', 220.30, 220.30),
            ('ORCL', 'Oracle Corp.', 115.40, 115.40),
            ('IBM', 'IBM Corp.', 145.20, 145.20),
            ('JPM', 'JPMorgan Chase', 150.30, 150.30),
            ('BAC', 'Bank of America', 35.20, 35.20),
            ('WFC', 'Wells Fargo', 48.50, 48.50),
            ('C', 'Citigroup Inc.', 52.30, 52.30),
            ('GS', 'Goldman Sachs', 380.40, 380.40),
            ('V', 'Visa Inc.', 240.20, 240.20),
            ('MA', 'Mastercard Inc.', 390.10, 390.10),
            ('JNJ', 'Johnson & Johnson', 160.40, 160.40),
            ('PFE', 'Pfizer Inc.', 28.30, 28.30),
            ('MRK', 'Merck & Co.', 115.20, 115.20),
            ('ABBV', 'AbbVie Inc.', 155.30, 155.30),
            ('WMT', 'Walmart Inc.', 145.20, 145.20),
            ('COST', 'Costco Wholesale', 520.30, 520.30),
            ('HD', 'Home Depot Inc.', 330.20, 330.20),
            ('MCD', 'McDonalds Corp.', 280.40, 280.40),
            ('SBUX', 'Starbucks Corp.', 92.30, 92.30)
        ]
        cursor.executemany(
            "INSERT INTO companies (ticker, name, price, prev_price) VALUES (?, ?, ?, ?)",
            companies
        )
    
    # Проверяем промокоды
    cursor.execute("SELECT COUNT(*) FROM promocodes")
    if cursor.fetchone()[0] == 0:
        promos = [
            ('WELCOME100', 100, 10, 0),
            ('START500', 500, 10, 0)
        ]
        cursor.executemany(
            "INSERT INTO promocodes (code, bonus, max_uses, used_count) VALUES (?, ?, ?, ?)",
            promos
        )
    
    # Проверяем сезон
    cursor.execute("SELECT COUNT(*) FROM season")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        end = now + timedelta(days=14)
        cursor.execute(
            "INSERT INTO season (id, name, start_date, end_date, active) VALUES (1, ?, ?, ?, 1)",
            ('ВЕСНА', now.isoformat(), end.isoformat())
        )

# ========== ПОЛЬЗОВАТЕЛИ ==========

def get_user(user_id, username=None):
    """Получить данные пользователя (создать если нет)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Создаем нового пользователя
        name = username or f"User_{user_id}"
        cursor.execute(
            "INSERT INTO users (user_id, username, money, day) VALUES (?, ?, 1000.0, 1)",
            (user_id, name)
        )
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        # Обновляем username если изменился
        if username and user['username'] != username:
            cursor.execute(
                "UPDATE users SET username = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?",
                (username, user_id)
            )
            conn.commit()
        else:
            # Просто обновляем last_seen
            cursor.execute(
                "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
    
    # Получаем портфель пользователя
    cursor.execute("SELECT ticker, amount FROM portfolio WHERE user_id = ?", (user_id,))
    portfolio_rows = cursor.fetchall()
    portfolio = {row['ticker']: row['amount'] for row in portfolio_rows}
    
    # Получаем инвентарь
    cursor.execute("SELECT * FROM inventory WHERE user_id = ? ORDER BY acquired_at", (user_id,))
    inventory = cursor.fetchall()
    
    # Получаем активные эффекты
    cursor.execute("SELECT * FROM active_effects WHERE user_id = ?", (user_id,))
    effects = cursor.fetchone()
    
    # Получаем подписки
    cursor.execute("SELECT * FROM subscriptions WHERE user_id = ? AND end_date > ?", 
                  (user_id, datetime.now().isoformat()))
    subscriptions = cursor.fetchall()
    
    conn.close()
    
    # Превращаем Row в словарь и добавляем доп поля
    user_dict = dict(user)
    user_dict['portfolio'] = portfolio
    user_dict['inventory'] = [dict(item) for item in inventory] if inventory else []
    user_dict['active_effects'] = dict(effects) if effects else {}
    user_dict['subscriptions'] = [dict(sub) for sub in subscriptions] if subscriptions else []
    
    return user_dict

def update_user_money(user_id, amount):
    """Изменить деньги пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (amount, user_id)
    )
    conn.commit()
    conn.close()

def update_user_day(user_id):
    """Увеличить день пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET day = day + 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

# ========== ПОРТФЕЛЬ ==========

def buy_stock(user_id, ticker, amount, price):
    """Купить акции"""
    conn = get_db()
    cursor = conn.cursor()
    
    total = price * amount
    
    # Проверяем, есть ли уже такие акции
    cursor.execute(
        "SELECT amount FROM portfolio WHERE user_id = ? AND ticker = ?",
        (user_id, ticker)
    )
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute(
            "UPDATE portfolio SET amount = amount + ? WHERE user_id = ? AND ticker = ?",
            (amount, user_id, ticker)
        )
    else:
        cursor.execute(
            "INSERT INTO portfolio (user_id, ticker, amount) VALUES (?, ?, ?)",
            (user_id, ticker, amount)
        )
    
    # Списываем деньги
    cursor.execute(
        "UPDATE users SET money = money - ? WHERE user_id = ?",
        (total, user_id)
    )
    
    conn.commit()
    conn.close()

def sell_stock(user_id, ticker, amount, price):
    """Продать акции"""
    conn = get_db()
    cursor = conn.cursor()
    
    total = price * amount
    
    cursor.execute(
        "UPDATE portfolio SET amount = amount - ? WHERE user_id = ? AND ticker = ?",
        (amount, user_id, ticker)
    )
    
    # Удаляем запись если акций стало 0
    cursor.execute(
        "DELETE FROM portfolio WHERE user_id = ? AND ticker = ? AND amount <= 0",
        (user_id, ticker)
    )
    
    # Начисляем деньги
    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (total, user_id)
    )
    
    conn.commit()
    conn.close()

def get_portfolio(user_id):
    """Получить портфель пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.ticker, p.amount, c.name, c.price 
        FROM portfolio p
        JOIN companies c ON p.ticker = c.ticker
        WHERE p.user_id = ?
    """, (user_id,))
    
    portfolio = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in portfolio]

# ========== КОМПАНИИ ==========

def get_all_companies():
    """Получить все компании"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies ORDER BY ticker")
    companies = cursor.fetchall()
    conn.close()
    return [dict(row) for row in companies]

def update_company_prices():
    """Обновить цены компаний"""
    import random
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT ticker, price FROM companies")
    companies = cursor.fetchall()
    
    for company in companies:
        old = company['price']
        change = random.uniform(-0.1, 0.1)
        new = round(old * (1 + change), 2)
        
        cursor.execute(
            "UPDATE companies SET prev_price = ?, price = ? WHERE ticker = ?",
            (old, new, company['ticker'])
        )
    
    conn.commit()
    conn.close()

def get_companies_page(page=1, per_page=10):
    """Получить страницу компаний"""
    companies = get_all_companies()
    total = len(companies)
    start = (page - 1) * per_page
    return companies[start:start+per_page], total

# ========== ИНВЕНТАРЬ ==========

def add_to_inventory(user_id, item):
    """Добавить предмет в инвентарь"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO inventory (user_id, item_id, name, emoji, description, category, effect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, item['item_id'], item['name'], item['emoji'], 
          item['description'], item['category'], item['effect']))
    
    conn.commit()
    conn.close()

def remove_from_inventory(user_id, item_id):
    """Удалить предмет из инвентаря (по id)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM inventory WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    )
    
    conn.commit()
    conn.close()

def get_inventory(user_id):
    """Получить инвентарь пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM inventory WHERE user_id = ? ORDER BY acquired_at",
        (user_id,)
    )
    inventory = cursor.fetchall()
    conn.close()
    
    return [dict(item) for item in inventory]

# ========== ПРОМОКОДЫ ==========

def get_all_promocodes():
    """Получить все промокоды"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promocodes")
    promos = cursor.fetchall()
    conn.close()
    return [dict(promo) for promo in promos]

def get_promocode(code):
    """Получить конкретный промокод"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promocodes WHERE code = ?", (code.upper(),))
    promo = cursor.fetchone()
    conn.close()
    return dict(promo) if promo else None

def add_promocode(code, bonus, max_uses):
    """Добавить новый промокод (для админа)"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO promocodes (code, bonus, max_uses, used_count) VALUES (?, ?, ?, 0)",
            (code.upper(), bonus, max_uses)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_promocode(code):
    """Удалить промокод (для админа)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM promocodes WHERE code = ?", (code.upper(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def use_promo(user_id, code):
    """Активировать промокод"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем промокод
    cursor.execute("SELECT * FROM promocodes WHERE code = ?", (code.upper(),))
    promo = cursor.fetchone()
    
    if not promo:
        conn.close()
        return False, "❌ Промокод не найден"
    
    if promo['used_count'] >= promo['max_uses']:
        conn.close()
        return False, "❌ Промокод закончился"
    
    # Проверяем, не использовал ли уже
    cursor.execute(
        "SELECT * FROM used_promos WHERE user_id = ? AND promo_code = ?",
        (user_id, code.upper())
    )
    if cursor.fetchone():
        conn.close()
        return False, "❌ Ты уже активировал этот промокод"
    
    # Начисляем бонус
    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (promo['bonus'], user_id)
    )
    
    # Отмечаем использованный
    cursor.execute(
        "INSERT INTO used_promos (user_id, promo_code) VALUES (?, ?)",
        (user_id, code.upper())
    )
    
    # Увеличиваем счетчик
    cursor.execute(
        "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
        (code.upper(),)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ +${promo['bonus']}"

# ========== ЛИДЕРЫ ==========

def update_leaderboard():
    """Обновить таблицу лидеров (просто возвращает топ)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем всех пользователей с их капиталом
    cursor.execute("SELECT user_id, username, money, cubes FROM users")
    users = cursor.fetchall()
    
    leaderboard = []
    for user in users:
        # Считаем стоимость акций
        cursor.execute("""
            SELECT SUM(p.amount * c.price) as stock_value
            FROM portfolio p
            JOIN companies c ON p.ticker = c.ticker
            WHERE p.user_id = ?
        """, (user['user_id'],))
        
        stock_value = cursor.fetchone()[0] or 0
        total_capital = user['money'] + stock_value
        
        leaderboard.append({
            'user_id': user['user_id'],
            'username': user['username'] or f"User_{user['user_id']}",
            'capital': round(total_capital, 2),
            'cubes': user['cubes']
        })
    
    conn.close()
    
    # Сортируем по капиталу
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    return leaderboard

def get_leaderboard(limit=10):
    """Получить топ пользователей"""
    leaderboard = update_leaderboard()
    return leaderboard[:limit]

# ========== СЕЗОН ==========

def get_current_season():
    """Получить текущий сезон"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM season WHERE id = 1")
    season = cursor.fetchone()
    conn.close()
    return dict(season) if season else None

def create_season(name, days):
    """Создать новый сезон"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    end = now + timedelta(days=days)
    
    cursor.execute("""
        UPDATE season SET name = ?, start_date = ?, end_date = ?, active = 1 WHERE id = 1
    """, (name, now.isoformat(), end.isoformat()))
    
    conn.commit()
    conn.close()

def end_season():
    """Завершить сезон и наградить победителей"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем топ-3
    leaderboard = get_leaderboard(50)
    top3 = leaderboard[:3]
    
    for i, user in enumerate(top3, 1):
        # Добавляем кубок
        cursor.execute(
            "UPDATE users SET cubes = cubes + 1 WHERE user_id = ?",
            (user['user_id'],)
        )
        
        # Добавляем в инвентарь
        cursor.execute("""
            INSERT INTO inventory (user_id, item_id, name, emoji, description, category, effect)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user['user_id'],
            'cube',
            f'Кубок {i} места',
            '🏆',
            f'Награда за {i} место в сезоне',
            'special',
            'cube'
        ))
    
    # Деактивируем сезон
    cursor.execute("UPDATE season SET active = 0 WHERE id = 1")
    
    conn.commit()
    conn.close()
    
    return True, "✅ Сезон завершён"

def get_season_time_left():
    """Сколько осталось до конца сезона"""
    season = get_current_season()
    if not season or not season['active']:
        return None, None
    
    end = datetime.fromisoformat(season['end_date'])
    now = datetime.now()
    
    if now > end:
        end_season()
        return None, None
    
    delta = end - now
    return delta.days, delta.seconds // 3600