import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config import DB_CONFIG

def get_db():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        cursor_factory=RealDictCursor
    )

def init_database():
    """Создание всех таблиц"""
    conn = get_db()
    cur = conn.cursor()
    
    # Пользователи
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            money DECIMAL(10,2) DEFAULT 10000.0,
            day INTEGER DEFAULT 1,
            cubes INTEGER DEFAULT 0,
            shields INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referrer_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Портфель
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            ticker TEXT,
            amount INTEGER DEFAULT 0,
            buy_price DECIMAL(10,2),
            bought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ticker)
        )
    """)
    
    # Инвентарь
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            item_id TEXT,
            item_name TEXT,
            item_emoji TEXT,
            category TEXT,
            acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Компании
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            price DECIMAL(10,2),
            prev_price DECIMAL(10,2)
        )
    """)
    
    # История цен
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            ticker TEXT REFERENCES companies(ticker),
            price DECIMAL(10,2),
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Транзакции
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            from_user BIGINT REFERENCES users(user_id),
            to_user BIGINT REFERENCES users(user_id),
            amount DECIMAL(10,2),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Достижения
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            achievement_id TEXT,
            achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, achievement_id)
        )
    """)
    
    # Промокоды
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            bonus DECIMAL(10,2),
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Использованные промокоды
    cur.execute("""
        CREATE TABLE IF NOT EXISTS used_promos (
            user_id BIGINT REFERENCES users(user_id),
            promo_code TEXT REFERENCES promocodes(code),
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, promo_code)
        )
    """)
    
    # Сезон
    cur.execute("""
        CREATE TABLE IF NOT EXISTS season (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            active BOOLEAN DEFAULT TRUE,
            CONSTRAINT one_row CHECK (id = 1)
        )
    """)
    
    conn.commit()
    conn.close()
    
    init_companies()
    init_season()

def init_companies():
    """Заполняем компании"""
    DEFAULT_COMPANIES = {
        'AAPL': ('Apple Inc.', 175.50),
        'MSFT': ('Microsoft Corp.', 330.25),
        'GOOG': ('Alphabet (Google)', 2800.75),
        'AMZN': ('Amazon.com Inc.', 3450.00),
        'META': ('Meta Platforms', 310.80),
        'NVDA': ('NVIDIA Corp.', 890.60),
        'TSLA': ('Tesla Inc.', 240.50),
        'JPM': ('JPMorgan Chase', 150.30),
        'V': ('Visa Inc.', 240.20),
        'WMT': ('Walmart Inc.', 145.20)
    }
    
    conn = get_db()
    cur = conn.cursor()
    
    for ticker, (name, price) in DEFAULT_COMPANIES.items():
        cur.execute("""
            INSERT INTO companies (ticker, name, price, prev_price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ticker) DO NOTHING
        """, (ticker, name, price, price))
    
    conn.commit()
    conn.close()

def init_season():
    """Создаем первый сезон"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM season")
    if cur.fetchone()['count'] == 0:
        start = datetime.now()
        end = start + timedelta(days=14)
        cur.execute("""
            INSERT INTO season (name, start_date, end_date)
            VALUES (%s, %s, %s)
        """, ('ВЕСНА', start, end))
    
    conn.commit()
    conn.close()

# ========== ПОЛЬЗОВАТЕЛИ ==========

def get_user(user_id, username=None, first_name=None):
    """Получить или создать пользователя"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, money)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (user_id, username, first_name, START_MONEY))
        user = cur.fetchone()
        conn.commit()
    else:
        if username or first_name:
            cur.execute("""
                UPDATE users 
                SET username = COALESCE(%s, username),
                    first_name = COALESCE(%s, first_name),
                    last_seen = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (username, first_name, user_id))
            conn.commit()
    
    conn.close()
    return user

def update_money(user_id, amount):
    """Изменить баланс"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET money = money + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    conn.close()

def transfer_money(from_id, to_username, amount):
    """Перевод денег другому пользователю"""
    conn = get_db()
    cur = conn.cursor()
    
    # Ищем получателя
    cur.execute("SELECT user_id, money FROM users WHERE username = %s", (to_username.replace('@', ''),))
    to_user = cur.fetchone()
    
    if not to_user:
        conn.close()
        return False, "❌ Пользователь не найден"
    
    # Проверяем баланс
    cur.execute("SELECT money FROM users WHERE user_id = %s", (from_id,))
    from_user = cur.fetchone()
    
    if from_user['money'] < amount:
        conn.close()
        return False, f"❌ Недостаточно средств. Нужно ${amount}"
    
    if amount <= 0:
        conn.close()
        return False, "❌ Сумма должна быть больше 0"
    
    # Переводим
    cur.execute("UPDATE users SET money = money - %s WHERE user_id = %s", (amount, from_id))
    cur.execute("UPDATE users SET money = money + %s WHERE user_id = %s", (amount, to_user['user_id']))
    
    # Логируем
    cur.execute("""
        INSERT INTO transactions (from_user, to_user, amount, description)
        VALUES (%s, %s, %s, %s)
    """, (from_id, to_user['user_id'], amount, 'Перевод'))
    
    conn.commit()
    conn.close()
    
    return True, f"✅ Переведено ${amount} пользователю @{to_username}"

# ========== ДОСТИЖЕНИЯ ==========

ACHIEVEMENTS = {
    'first_trade': {'name': 'Первая сделка', 'emoji': '🎯', 'desc': 'Соверши первую покупку'},
    'trader_10': {'name': 'Трейдер', 'emoji': '📊', 'desc': 'Соверши 10 сделок'},
    'trader_100': {'name': 'Профи', 'emoji': '📈', 'desc': 'Соверши 100 сделок'},
    'capital_10k': {'name': 'Инвестор', 'emoji': '💰', 'desc': 'Накопи 10,000$'},
    'capital_100k': {'name': 'Богач', 'emoji': '💎', 'desc': 'Накопи 100,000$'},
    'millionaire': {'name': 'Миллионер', 'emoji': '👑', 'desc': 'Накопи 1,000,000$'},
    'first_cube': {'name': 'Победитель', 'emoji': '🥇', 'desc': 'Получи первый кубок'},
    'referral_5': {'name': 'Лидер', 'emoji': '👥', 'desc': 'Пригласи 5 друзей'}
}

def check_achievements(user_id):
    """Проверить и выдать достижения"""
    conn = get_db()
    cur = conn.cursor()
    
    # Получаем данные пользователя
    cur.execute("""
        SELECT u.*, 
               COUNT(DISTINCT t.id) as trades,
               (SELECT COUNT(*) FROM users WHERE referrer_id = u.user_id) as refs
        FROM users u
        LEFT JOIN transactions t ON u.user_id = t.from_user
        WHERE u.user_id = %s
        GROUP BY u.user_id
    """, (user_id,))
    user = cur.fetchone()
    
    if not user:
        conn.close()
        return []
    
    new_achievements = []
    
    # Проверяем каждое достижение
    checks = [
        ('first_trade', user['trades'] >= 1),
        ('trader_10', user['trades'] >= 10),
        ('trader_100', user['trades'] >= 100),
        ('capital_10k', user['money'] >= 10000),
        ('capital_100k', user['money'] >= 100000),
        ('millionaire', user['money'] >= 1000000),
        ('first_cube', user['cubes'] >= 1),
        ('referral_5', user['refs'] >= 5)
    ]
    
    for ach_id, condition in checks:
        if condition:
            try:
                cur.execute("""
                    INSERT INTO achievements (user_id, achievement_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, achievement_id) DO NOTHING
                    RETURNING *
                """, (user_id, ach_id))
                if cur.fetchone():
                    new_achievements.append(ach_id)
            except:
                pass
    
    conn.commit()
    conn.close()
    
    return new_achievements

# ========== КОМПАНИИ ==========

def update_prices():
    """Обновить цены компаний"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT ticker, price FROM companies")
    companies = cur.fetchall()
    
    for comp in companies:
        change = random.uniform(-0.1, 0.1)
        new_price = round(comp['price'] * (1 + change), 2)
        
        cur.execute("""
            UPDATE companies 
            SET prev_price = price, price = %s 
            WHERE ticker = %s
        """, (new_price, comp['ticker']))
        
        cur.execute("""
            INSERT INTO price_history (ticker, price)
            VALUES (%s, %s)
        """, (comp['ticker'], new_price))
    
    conn.commit()
    conn.close()

def get_portfolio(user_id):
    """Портфель пользователя"""
    conn = get_db()
    cur = conn.execute("""
        SELECT p.*, c.name, c.price 
        FROM portfolio p
        JOIN companies c ON p.ticker = c.ticker
        WHERE p.user_id = %s
    """, (user_id,))
    portfolio = cur.fetchall()
    conn.close()
    return portfolio

# ========== ЛИДЕРЫ ==========

def get_leaderboard(limit=10):
    """Топ игроков"""
    conn = get_db()
    cur = conn.execute("""
        SELECT 
            u.user_id,
            u.username,
            u.first_name,
            u.money,
            u.cubes,
            COALESCE(SUM(p.amount * c.price), 0) as stock_value,
            (u.money + COALESCE(SUM(p.amount * c.price), 0)) as total
        FROM users u
        LEFT JOIN portfolio p ON u.user_id = p.user_id
        LEFT JOIN companies c ON p.ticker = c.ticker
        GROUP BY u.user_id, u.username, u.first_name, u.money, u.cubes
        ORDER BY total DESC
        LIMIT %s
    """, (limit,))
    leaders = cur.fetchall()
    conn.close()
    return leaders

# ========== АДМИН-ФУНКЦИИ ==========

def get_stats():
    """Статистика бота"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()['count']
    
    cur.execute("""
        SELECT COUNT(*) FROM users 
        WHERE last_seen > CURRENT_TIMESTAMP - INTERVAL '1 day'
    """)
    active = cur.fetchone()['count']
    
    cur.execute("SELECT SUM(money) FROM users")
    total_money = cur.fetchone()['sum'] or 0
    
    cur.execute("SELECT SUM(amount * price) FROM portfolio p JOIN companies c ON p.ticker = c.ticker")
    total_stocks = cur.fetchone()['sum'] or 0
    
    cur.execute("SELECT COUNT(*) FROM transactions")
    trades = cur.fetchone()['count']
    
    cur.execute("SELECT SUM(referrals) FROM users")
    total_refs = cur.fetchone()['sum'] or 0
    
    conn.close()
    
    return {
        'users': users,
        'active': active,
        'total_money': total_money,
        'total_stocks': total_stocks,
        'total_capital': total_money + total_stocks,
        'trades': trades,
        'total_refs': total_refs
    }