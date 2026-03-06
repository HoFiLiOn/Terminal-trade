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
SEASON_FILE = "season.json"
BROADCAST_LOG = "broadcast_log.json"

if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== КАРТИНКИ ДЛЯ БОТА ==========
IMAGES = {
    'main': 'https://s10.iimage.su/s/05/gIKluIYxLgUpL28XWRh1IzTmdY4DzqMQuX8v39ee9.jpg',
    'companies': 'https://s10.iimage.su/s/05/gf3a1gxxMZn6ArfLKZD3JlzVhy83Bm1cGvNVjC0vI.jpg',
    'stats': 'https://s10.iimage.su/s/05/gioJHlUxz7G3Udtvbpc4t3CAoCSsryhLnSFXWdayc.jpg',
    'inventory': 'https://s10.iimage.su/s/05/grMXdR3xwFaLXdQ74TR9rz7zu8Wb60ezeX89JKuzm.jpg',
    'shop': 'https://s10.iimage.su/s/05/gbuaUsrxIjSjwQcGwcZrUaNcbFXzpITC2qFzhFzrd.jpg',
    'leaderboard': 'https://s10.iimage.su/s/05/gYoBW3cxowvFLbKdb8GJCDKWoEAcQD5DJa0zHCQt6.jpg'
}

# ========== 30 КОМПАНИЙ ==========
DEFAULT_COMPANIES = {
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
    'JPM': {'name': 'JPMorgan Chase', 'price': 150.30, 'prev_price': 150.30},
    'BAC': {'name': 'Bank of America', 'price': 35.20, 'prev_price': 35.20},
    'WFC': {'name': 'Wells Fargo', 'price': 48.50, 'prev_price': 48.50},
    'C': {'name': 'Citigroup Inc.', 'price': 52.30, 'prev_price': 52.30},
    'GS': {'name': 'Goldman Sachs', 'price': 380.40, 'prev_price': 380.40},
    'V': {'name': 'Visa Inc.', 'price': 240.20, 'prev_price': 240.20},
    'MA': {'name': 'Mastercard Inc.', 'price': 390.10, 'prev_price': 390.10},
    'JNJ': {'name': 'Johnson & Johnson', 'price': 160.40, 'prev_price': 160.40},
    'PFE': {'name': 'Pfizer Inc.', 'price': 28.30, 'prev_price': 28.30},
    'MRK': {'name': 'Merck & Co.', 'price': 115.20, 'prev_price': 115.20},
    'ABBV': {'name': 'AbbVie Inc.', 'price': 155.30, 'prev_price': 155.30},
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

# ========== СЕЗОН ==========
DEFAULT_SEASON = {
    'name': 'ВЕСНА',
    'start': str(datetime.now()),
    'end': str(datetime.now() + timedelta(days=14)),
    'active': True
}

# ========== ТОВАРЫ МАГАЗИНА ==========
SHOP_ITEMS = {
    'booster': {
        'name': 'Ускоритель',
        'description': 'Цены будут расти на 50% быстрее в течение 1 дня',
        'price': 500,
        'emoji': '🚀',
        'effect': 'booster'
    },
    'shield': {
        'name': 'Страховка',
        'description': 'Защищает от убытков (одна неудачная сделка не съест деньги)',
        'price': 300,
        'emoji': '🛡️',
        'effect': 'shield'
    },
    'analyst': {
        'name': 'Аналитик',
        'description': 'Покажет следующее изменение цены для выбранной компании',
        'price': 200,
        'emoji': '📊',
        'effect': 'analyst'
    },
    'random': {
        'name': 'Рандом',
        'description': 'Случайный бонус (может быть как плюс, так и минус)',
        'price': 100,
        'emoji': '🎲',
        'effect': 'random'
    },
    'vip': {
        'name': 'VIP статус',
        'description': 'Особая роль в чате и +10% к доходу навсегда',
        'price': 5000,
        'emoji': '💎',
        'effect': 'vip'
    },
    'lucky_box': {
        'name': 'Лаки бокс',
        'description': 'Случайный предмет',
        'price': 300,
        'emoji': '🎁',
        'effect': 'lucky_box'
    }
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
            user = json.load(f)
            if 'inventory' not in user:
                user['inventory'] = []
            if 'cubes' not in user:
                user['cubes'] = 0
            if 'effects' not in user:
                user['effects'] = {}
            return user
    else:
        user_data = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'username': None,
            'first_seen': str(datetime.now()),
            'last_seen': str(datetime.now()),
            'used_promos': [],
            'inventory': [],
            'cubes': 0,
            'effects': {}
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

def buy_item(user_id, item_id):
    user = get_user(user_id)
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        return False, "❌ Товар не найден"
    
    if item['price'] > user['money']:
        return False, f"❌ Недостаточно денег. Нужно ${item['price']}"
    
    user['money'] -= item['price']
    user['money'] = round(user['money'], 2)
    
    if 'inventory' not in user:
        user['inventory'] = []
    
    user['inventory'].append({
        'item_id': item_id,
        'name': item['name'],
        'emoji': item['emoji'],
        'description': item['description'],
        'effect': item.get('effect', ''),
        'bought_at': str(datetime.now())
    })
    
    save_user(user_id, user)
    return True, f"✅ Ты купил {item['emoji']} {item['name']}!"

def activate_item(user_id, item_index):
    user = get_user(user_id)
    
    if item_index < 0 or item_index >= len(user['inventory']):
        return False, "❌ Предмет не найден"
    
    item = user['inventory'][item_index]
    effect = item.get('effect', '')
    
    if effect == 'booster':
        user['effects']['booster'] = True
        msg = "🚀 Ускоритель активирован!"
    elif effect == 'shield':
        user['effects']['shield'] = user['effects'].get('shield', 0) + 1
        msg = "🛡️ Страховка активирована!"
    elif effect == 'analyst':
        msg = "📊 Аналитик: рынок будет расти!"
    elif effect == 'random':
        bonus = random.randint(-200, 500)
        user['money'] += bonus
        msg = f"🎲 Рандом: ты {'получил' if bonus > 0 else 'потерял'} ${abs(bonus)}"
    elif effect == 'vip':
        user['effects']['vip'] = True
        msg = "💎 VIP статус активирован!"
    elif effect == 'lucky_box':
        items = list(SHOP_ITEMS.keys())
        random_item = random.choice(items)
        user['inventory'].append({
            'item_id': random_item,
            'name': SHOP_ITEMS[random_item]['name'],
            'emoji': SHOP_ITEMS[random_item]['emoji'],
            'description': SHOP_ITEMS[random_item]['description'],
            'effect': SHOP_ITEMS[random_item].get('effect', ''),
            'bought_at': str(datetime.now())
        })
        msg = f"🎁 Тебе выпал: {SHOP_ITEMS[random_item]['emoji']} {SHOP_ITEMS[random_item]['name']}!"
    else:
        return False, "❌ Неизвестный эффект"
    
    save_user(user_id, user)
    user['inventory'].pop(item_index)
    save_user(user_id, user)
    
    return True, msg

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
                'day': user['day'],
                'cubes': user.get('cubes', 0)
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

# ========== СЕЗОНЫ ==========
def get_current_season():
    season = load_json(SEASON_FILE)
    if not season:
        season = DEFAULT_SEASON.copy()
        save_json(SEASON_FILE, season)
    return season

def create_season(name, days):
    season = {
        'name': name,
        'start': str(datetime.now()),
        'end': str(datetime.now() + timedelta(days=days)),
        'active': True
    }
    save_json(SEASON_FILE, season)
    return season

def end_season():
    season = get_current_season()
    if not season['active']:
        return False, "❌ Сезон уже завершён"
    
    season['active'] = False
    save_json(SEASON_FILE, season)
    
    leaderboard = get_leaderboard(3)
    for i, entry in enumerate(leaderboard, 1):
        user = get_user(entry['user_id'])
        user['cubes'] = user.get('cubes', 0) + 1
        if 'inventory' not in user:
            user['inventory'] = []
        user['inventory'].append({
            'item_id': 'cube',
            'name': f'{season["name"]} Кубок',
            'emoji': '🏆',
            'place': i,
            'season': season['name'],
            'bought_at': str(datetime.now())
        })
        save_user(entry['user_id'], user)
    
    return True, f"✅ Сезон завершён! Награды выданы топ-3"

def get_season_time_left():
    season = get_current_season()
    if not season or not season.get('active'):
        return None, None
    
    end = datetime.fromisoformat(season['end'])
    now = datetime.now()
    
    if now > end:
        end_season()
        return None, None
    
    days = (end - now).days
    hours = ((end - now).seconds // 3600)
    return days, hours

def season_check_loop():
    while True:
        time.sleep(3600)
        season = get_current_season()
        if season.get('active'):
            days_left, _ = get_season_time_left()
            if days_left is None:
                end_season()

threading.Thread(target=season_check_loop, daemon=True).start()

# ========== РАССЫЛКИ ==========
def broadcast_to_all(text):
    sent = 0
    failed = 0
    
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = int(filename.replace('.json', ''))
            try:
                bot.send_message(user_id, f"📢 {text}")
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1
    
    return sent, failed

def broadcast_to_active(text):
    sent = 0
    failed = 0
    today = datetime.now().date()
    
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            user_id = int(filename.replace('.json', ''))
            try:
                user = get_user(user_id)
                last_seen = datetime.fromisoformat(user.get('last_seen', '2000-01-01')).date()
                
                if last_seen == today:
                    bot.send_message(user_id, f"📢 {text}")
                    sent += 1
                else:
                    failed += 1
                time.sleep(0.05)
            except:
                failed += 1
    
    return sent, failed

# ========== КНОПКИ ==========
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="status"),
        types.InlineKeyboardButton("📈 Компании", callback_data="list"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🎟️ Промо", callback_data="promo"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("◀️ Назад", callback_data="back")
    markup.add(btn)
    return markup

def get_shop_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for item_id, item in SHOP_ITEMS.items():
        markup.add(
            types.InlineKeyboardButton(
                f"{item['emoji']} {item['name']} — ${item['price']}",
                callback_data=f"shop_{item_id}"
            )
        )
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back"))
    return markup

def get_inventory_keyboard(user):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i, item in enumerate(user.get('inventory', [])):
        markup.add(
            types.InlineKeyboardButton(
                f"{item['emoji']} {item['name']}",
                callback_data=f"inv_{i}"
            )
        )
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back"))
    return markup

def get_companies_keyboard(current_page, total_pages):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if total_pages > 1:
        btn1 = types.InlineKeyboardButton("◀️", callback_data=f"page_{current_page-1}")
        btn2 = types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        btn3 = types.InlineKeyboardButton("▶️", callback_data=f"page_{current_page+1}")
        markup.add(btn1, btn2, btn3)
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back"))
    return markup

# ========== КОМАНДЫ ДЛЯ ИГРОКОВ ==========
@bot.message_handler(commands=['start', 'trade'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    user = get_user(user_id)
    user['username'] = username
    user['last_seen'] = str(datetime.now())
    save_user(user_id, user)
    
    season = get_current_season()
    days_left, hours_left = get_season_time_left()
    
    time_left = ""
    if days_left is not None:
        time_left = f"\n📅 До конца сезона: {days_left}д {hours_left}ч"
    
    story = (
        "📜 *Небольшая предыстория...*\n\n"
        "Ты обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота. "
        "В описании было сказано: _«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»_.\n\n"
        "Сначала ты подумал, что это очередной развод, но любопытство взяло верх. "
        "Ты запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.\n\n"
        "Теперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.\n\n"
        "Добро пожаловать в Terminal Trade."
    )
    
    caption = f"""
{story}

💰 Твой баланс: ${user['money']:,.2f}
🏆 Кубков: {user.get('cubes', 0)}
{time_left}

Используй /help для списка команд
    """
    
    if IMAGES.get('main'):
        bot.send_photo(
            message.chat.id,
            IMAGES['main'],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(message.chat.id, caption, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "❓ *Помощь по Terminal Trade*\n\n"
        "*Основные команды:*\n"
        "• /trade — начать игру\n"
        "• /tbuy AAPL 5 — купить акции\n"
        "• /tsell TSLA 2 — продать акции\n"
        "• /tnext — следующий день\n"
        "• /tlist — список компаний\n"
        "• /tstats — твоя статистика\n"
        "• /tleader — таблица лидеров\n\n"
        "*Экономика:*\n"
        "• /shop — магазин предметов\n"
        "• /inventory — инвентарь\n"
        "• /tpromo КОД — активировать промокод\n"
        "• /promo — список промокодов"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

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
            btn1 = types.InlineKeyboardButton("✅ Активировать", callback_data=f"confirm_{promo_code}")
            btn2 = types.InlineKeyboardButton("❌ Отмена", callback_data="back")
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
    
    if IMAGES.get('companies'):
        bot.send_photo(
            message.chat.id,
            IMAGES['companies'],
            caption=text,
            reply_markup=get_companies_keyboard(1, total_pages)
        )
    else:
        bot.send_message(message.chat.id, text, reply_markup=get_companies_keyboard(1, total_pages))

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
🏆 Кубков: {user.get('cubes', 0)}

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
    
    if IMAGES.get('stats'):
        bot.send_photo(
            message.chat.id,
            IMAGES['stats'],
            caption=text,
            reply_markup=get_main_keyboard()
        )
    else:
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
        text += f"{medal} {name} — ${entry['capital']:,.2f} (🏆 {entry.get('cubes', 0)})\n"
    
    if IMAGES.get('leaderboard'):
        bot.send_photo(
            message.chat.id,
            IMAGES['leaderboard'],
            caption=text,
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['inventory'])
def inventory_command(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    text = f"🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
    
    if user.get('inventory'):
        for i, item in enumerate(user['inventory'], 1):
            text += f"{i}. {item['emoji']} {item['name']}\n"
    else:
        text += "Пусто\n"
    
    text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
    
    if IMAGES.get('inventory'):
        bot.send_photo(
            message.chat.id,
            IMAGES['inventory'],
            caption=text,
            reply_markup=get_inventory_keyboard(user)
        )
    else:
        bot.send_message(message.chat.id, text, reply_markup=get_inventory_keyboard(user))

@bot.message_handler(commands=['shop'])
def shop_command(message):
    text = "🛒 МАГАЗИН\n\nВыбери товар:"
    
    if IMAGES.get('shop'):
        bot.send_photo(
            message.chat.id,
            IMAGES['shop'],
            caption=text,
            reply_markup=get_shop_keyboard()
        )
    else:
        bot.send_message(message.chat.id, text, reply_markup=get_shop_keyboard())

@bot.message_handler(commands=['promo'])
def promo_list_command(message):
    promos = load_promocodes()
    
    text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
    
    for code, data in promos.items():
        remaining = data['max_uses'] - data['used_count']
        text += f"`{code}` — +${data['bonus']} (осталось {remaining}/{data['max_uses']})\n"
    
    text += "\nАктивировать: /tpromo КОД"
    
    bot.send_message(message.chat.id, text, reply_markup=get_back_keyboard())

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    # Кнопка назад
    if call.data == "back":
        user = get_user(user_id)
        season = get_current_season()
        days_left, hours_left = get_season_time_left()
        
        time_left = ""
        if days_left is not None:
            time_left = f"\n📅 До конца сезона: {days_left}д {hours_left}ч"
        
        story = (
            "📜 *Небольшая предыстория...*\n\n"
            "Ты обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота. "
            "В описании было сказано: _«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»_.\n\n"
            "Сначала ты подумал, что это очередной развод, но любопытство взяло верх. "
            "Ты запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.\n\n"
            "Теперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.\n\n"
            "Добро пожаловать в Terminal Trade."
        )
        
        caption = f"""
{story}

💰 Твой баланс: ${user['money']:,.2f}
🏆 Кубков: {user.get('cubes', 0)}
{time_left}

Используй /help для списка команд
        """
        
        if IMAGES.get('main'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption=caption, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard()
            )
        else:
            bot.edit_message_text(
                caption,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        bot.answer_callback_query(call.id)
    
    # Статус
    elif call.data == "status":
        user = get_user(user_id)
        capital = calculate_capital(user_id)
        portfolio = get_portfolio(user_id)
        
        text = f"""
📊 ТВОЙ СТАТУС (День {user['day']})

💰 Баланс: ${user['money']:,.2f}
💵 Капитал: ${capital:,.2f}
🏆 Кубков: {user.get('cubes', 0)}

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
        
        if IMAGES.get('stats'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['stats'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        bot.answer_callback_query(call.id)
    
    # Компании
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
        
        if IMAGES.get('companies'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['companies'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_companies_keyboard(1, total_pages)
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_companies_keyboard(1, total_pages)
            )
        bot.answer_callback_query(call.id)
    
    # Следующий день
    elif call.data == "next":
        update_company_prices()
        user = get_user(user_id)
        user['day'] += 1
        user['last_seen'] = str(datetime.now())
        save_user(user_id, user)
        update_leaderboard()
        
        if IMAGES.get('main'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption="⏩ Новый день! Цены обновлены."),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        else:
            bot.edit_message_text(
                "⏩ Новый день! Цены обновлены.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        bot.answer_callback_query(call.id)
    
    # Лидеры
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
            text += f"{medal} {name} — ${entry['capital']:,.2f} (🏆 {entry.get('cubes', 0)})\n"
        
        if IMAGES.get('leaderboard'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['leaderboard'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_keyboard()
            )
        bot.answer_callback_query(call.id)
    
    # Магазин
    elif call.data == "shop":
        text = "🛒 МАГАЗИН\n\nВыбери товар:"
        
        if IMAGES.get('shop'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['shop'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_shop_keyboard()
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_shop_keyboard()
            )
        bot.answer_callback_query(call.id)
    
    # Товар в магазине
    elif call.data.startswith("shop_"):
        item_id = call.data.replace("shop_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            bot.answer_callback_query(call.id, "❌ Товар не найден")
            return
        
        user = get_user(user_id)
        
        text = f"""
{item['emoji']} *{item['name']}*

{item['description']}

💰 Цена: ${item['price']}
💳 Твой баланс: ${user['money']:,.2f}

Купить?
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Купить", callback_data=f"buy_{item_id}"),
            types.InlineKeyboardButton("◀️ Назад", callback_data="shop")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    # Покупка предмета
    elif call.data.startswith("buy_"):
        item_id = call.data.replace("buy_", "")
        
        success, msg = buy_item(user_id, item_id)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        
        if success:
            user = get_user(user_id)
            text = f"🛒 МАГАЗИН\n\n💰 Твой баланс: ${user['money']:,.2f}\n\nВыбери товар:"
            
            if IMAGES.get('shop'):
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['shop'], caption=text),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_shop_keyboard()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_shop_keyboard()
                )
    
    # Инвентарь
    elif call.data == "inventory":
        user = get_user(user_id)
        
        text = f"🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
        
        if user.get('inventory'):
            for i, item in enumerate(user['inventory'], 1):
                text += f"{i}. {item['emoji']} {item['name']}\n"
        else:
            text += "Пусто\n"
        
        text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
        
        if IMAGES.get('inventory'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['inventory'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_inventory_keyboard(user)
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_inventory_keyboard(user)
            )
        bot.answer_callback_query(call.id)
    
    # Предмет в инвентаре
    elif call.data.startswith("inv_"):
        item_index = int(call.data.replace("inv_", ""))
        user = get_user(user_id)
        
        if item_index >= len(user.get('inventory', [])):
            bot.answer_callback_query(call.id, "❌ Предмет не найден")
            return
        
        item = user['inventory'][item_index]
        
        text = f"""
{item['emoji']} *{item['name']}*

{item.get('description', '')}

Активировать?
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Активировать", callback_data=f"use_{item_index}"),
            types.InlineKeyboardButton("◀️ Назад", callback_data="inventory")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    # Использование предмета
    elif call.data.startswith("use_"):
        item_index = int(call.data.replace("use_", ""))
        
        success, msg = activate_item(user_id, item_index)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        
        if success:
            user = get_user(user_id)
            text = f"🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
            
            if user.get('inventory'):
                for i, item in enumerate(user['inventory'], 1):
                    text += f"{i}. {item['emoji']} {item['name']}\n"
            else:
                text += "Пусто\n"
            
            text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
            
            if IMAGES.get('inventory'):
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['inventory'], caption=text),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_inventory_keyboard(user)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_inventory_keyboard(user)
                )
    
    # Промокоды
    elif call.data == "promo":
        promos = load_promocodes()
        
        text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
        
        for code, data in promos.items():
            remaining = data['max_uses'] - data['used_count']
            text += f"`{code}` — +${data['bonus']} (осталось {remaining}/{data['max_uses']})\n"
        
        text += "\nАктивировать: /tpromo КОД"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    # Помощь
    elif call.data == "help":
        help_text = (
            "❓ *Помощь по Terminal Trade*\n\n"
            "*Основные команды:*\n"
            "• /trade — начать игру\n"
            "• /tbuy AAPL 5 — купить акции\n"
            "• /tsell TSLA 2 — продать акции\n"
            "• /tnext — следующий день\n"
            "• /tlist — список компаний\n"
            "• /tstats — твоя статистика\n"
            "• /tleader — таблица лидеров\n\n"
            "*Экономика:*\n"
            "• /shop — магазин предметов\n"
            "• /inventory — инвентарь\n"
            "• /tpromo КОД — активировать промокод\n"
            "• /promo — список промокодов"
        )
        
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    # Пагинация компаний
    elif call.data.startswith("page_"):
        page = int(call.data.replace("page_", ""))
        user = get_user(user_id)
        companies, total = get_companies_page(page=page)
        total_pages = (total + 9) // 10
        
        if page < 1 or page > total_pages:
            bot.answer_callback_query(call.id)
            return
        
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
        
        if IMAGES.get('companies'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['companies'], caption=text),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_companies_keyboard(page, total_pages)
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_companies_keyboard(page, total_pages)
            )
        bot.answer_callback_query(call.id)
    
    # Подтверждение промокода
    elif call.data.startswith("confirm_"):
        promo_code = call.data.replace("confirm_", "")
        
        success, msg = use_promo(user_id, promo_code)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        
        if success:
            update_user_last_seen(user_id)
            update_leaderboard()
        
        user = get_user(user_id)
        season = get_current_season()
        days_left, hours_left = get_season_time_left()
        
        time_left = ""
        if days_left is not None:
            time_left = f"\n📅 До конца сезона: {days_left}д {hours_left}ч"
        
        story = (
            "📜 *Небольшая предыстория...*\n\n"
            "Ты обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота. "
            "В описании было сказано: _«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»_.\n\n"
            "Сначала ты подумал, что это очередной развод, но любопытство взяло верх. "
            "Ты запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.\n\n"
            "Теперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.\n\n"
            "Добро пожаловать в Terminal Trade."
        )
        
        caption = f"""
{story}

💰 Твой баланс: ${user['money']:,.2f}
🏆 Кубков: {user.get('cubes', 0)}
{time_left}

Используй /help для списка команд
        """
        
        if IMAGES.get('main'):
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption=caption, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_keyboard()
            )
        else:
            bot.edit_message_text(
                caption,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # Заглушка для нераспознанных кнопок
    else:
        bot.answer_callback_query(call.id)

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['adminhelp'])
def admin_help(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Недостаточно прав")
        return
    
    text = """
👑 АДМИН-КОМАНДЫ

/admingive ID СУММА — выдать деньги
/admintake ID СУММА — забрать деньги
/adminreset ID — сбросить игрока
/adminpromo КОД БОНУС МАКС — добавить промокод
/adminpromodel КОД — удалить промокод
/adminpromos — список промокодов
/admincomps — список компаний
/adminseason НАЗВАНИЕ ДНЕЙ — создать сезон
/adminseasonend — завершить сезон
/adminstats — общая статистика
/admintop — топ-10
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['admingive'])
def admin_give(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = float(parts[2])
        
        user = get_user(target_id)
        user['money'] += amount
        save_user(target_id, user)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ Пользователю {target_id} выдано ${amount:,.2f}")
    except:
        bot.reply_to(message, "❌ Использование: /admingive ID СУММА")

@bot.message_handler(commands=['admintake'])
def admin_take(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = float(parts[2])
        
        user = get_user(target_id)
        user['money'] -= amount
        save_user(target_id, user)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ У пользователя {target_id} забрано ${amount:,.2f}")
    except:
        bot.reply_to(message, "❌ Использование: /admintake ID СУММА")

@bot.message_handler(commands=['adminreset'])
def admin_reset(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[1])
        
        user_data = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'username': None,
            'first_seen': str(datetime.now()),
            'last_seen': str(datetime.now()),
            'used_promos': [],
            'inventory': [],
            'cubes': 0,
            'effects': {}
        }
        save_user(target_id, user_data)
        update_leaderboard()
        
        bot.reply_to(message, f"✅ Пользователь {target_id} сброшен")
    except:
        bot.reply_to(message, "❌ Использование: /adminreset ID")

@bot.message_handler(commands=['adminpromo'])
def admin_promo_add(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        code = parts[1].upper()
        bonus = int(parts[2])
        max_uses = int(parts[3])
        
        success = add_promocode(code, bonus, max_uses)
        
        if success:
            bot.reply_to(message, f"✅ Промокод {code} добавлен (${bonus}, {max_uses} использований)")
        else:
            bot.reply_to(message, "❌ Промокод уже существует")
    except:
        bot.reply_to(message, "❌ Использование: /adminpromo КОД БОНУС МАКС")

@bot.message_handler(commands=['adminpromodel'])
def admin_promo_del(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        code = message.text.split()[1].upper()
        
        success = delete_promocode(code)
        
        if success:
            bot.reply_to(message, f"✅ Промокод {code} удален")
        else:
            bot.reply_to(message, "❌ Промокод не найден")
    except:
        bot.reply_to(message, "❌ Использование: /adminpromodel КОД")

@bot.message_handler(commands=['adminpromos'])
def admin_promos(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    promos = load_promocodes()
    
    if not promos:
        bot.reply_to(message, "📋 Нет промокодов")
        return
    
    text = "🎟️ ВСЕ ПРОМОКОДЫ\n\n"
    for code, data in promos.items():
        remaining = data['max_uses'] - data['used_count']
        text += f"{code} — ${data['bonus']} — {data['used_count']}/{data['max_uses']} (осталось {remaining})\n"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['admincomps'])
def admin_comps(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    companies = load_companies()
    
    text = "📋 ВСЕ КОМПАНИИ\n\n"
    for ticker, data in companies.items():
        text += f"{ticker} — {data['name']} — ${data['price']:,.2f}\n"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['adminseason'])
def admin_season_create(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        name = parts[1]
        days = int(parts[2])
        
        create_season(name, days)
        bot.reply_to(message, f"✅ Сезон '{name}' создан на {days} дней")
    except:
        bot.reply_to(message, "❌ Использование: /adminseason НАЗВАНИЕ ДНЕЙ")

@bot.message_handler(commands=['adminseasonend'])
def admin_season_end(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    success, msg = end_season()
    bot.reply_to(message, msg)

@bot.message_handler(commands=['adminstats'])
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
📊 ОБЩАЯ СТАТИСТИКА

👥 Всего игроков: {total_users}
💰 Всего денег: ${total_money:,.2f}
🎟️ Промокодов: {total_promos}
🎫 Активаций: {total_activations}
🏢 Компаний: {total_companies}
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['admintop'])
def admin_top(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    leaderboard = get_leaderboard(10)
    
    text = "🏆 ТОП-10 ПО КАПИТАЛУ\n\n"
    
    for i, entry in enumerate(leaderboard, 1):
        text += f"{i}. {entry['username']} — ${entry['capital']:,.2f}\n"
    
    bot.reply_to(message, text)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()