import telebot
from telebot import types
import random
import json
import os
from datetime import datetime, timedelta

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

if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== КАРТИНКИ ==========
IMAGES = {
    'main': 'https://s10.iimage.su/s/05/gIKluIYxLgUpL28XWRh1IzTmdY4DzqMQuX8v39ee9.jpg',
    'companies': 'https://s10.iimage.su/s/05/gf3a1gxxMZn6ArfLKZD3JlzVhy83Bm1cGvNVjC0vI.jpg',
    'stats': 'https://s10.iimage.su/s/05/gioJHlUxz7G3Udtvbpc4t3CAoCSsryhLnSFXWdayc.jpg',
    'inventory': 'https://s10.iimage.su/s/05/grMXdR3xwFaLXdQ74TR9rz7zu8Wb60ezeX89JKuzm.jpg',
    'shop': 'https://s10.iimage.su/s/05/gbuaUsrxIjSjwQcGwcZrUaNcbFXzpITC2qFzhFzrd.jpg',
    'leaderboard': 'https://s10.iimage.su/s/05/gYoBW3cxowvFLbKdb8GJCDKWoEAcQD5DJa0zHCQt6.jpg'
}

# ========== ТЕКСТ ==========
STORY = (
    "📜 *Небольшая предыстория...*\n\n"
    "Ты обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота.\n"
    "В описании было сказано: _«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»_.\n\n"
    "Сначала ты подумал, что это очередной развод, но любопытство взяло верх.\n"
    "Ты запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.\n\n"
    "Теперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.\n\n"
    "Добро пожаловать в *Terminal Trade*."
)

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
    "START500": {"bonus": 500, "max_uses": 10, "used_count": 0}
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
    # Расходники
    'booster': {
        'name': 'Ускоритель',
        'description': 'Цены будут расти на 50% быстрее 1 день',
        'price': 500,
        'emoji': '🚀',
        'category': 'consumable',
        'effect': 'booster'
    },
    'shield': {
        'name': 'Страховка',
        'description': 'Защита от 1 убытка',
        'price': 300,
        'emoji': '🛡️',
        'category': 'consumable',
        'effect': 'shield'
    },
    'analyst': {
        'name': 'Аналитик',
        'description': 'Прогноз цены на следующий день',
        'price': 200,
        'emoji': '📊',
        'category': 'consumable',
        'effect': 'analyst'
    },
    'random': {
        'name': 'Рандом',
        'description': 'Случайный бонус от $50 до $500',
        'price': 100,
        'emoji': '🎲',
        'category': 'consumable',
        'effect': 'random'
    },
    
    # ПОДПИСКИ
    'vip_month': {
        'name': 'VIP на месяц',
        'description': '30 дней: +10% к доходу',
        'price': 5000,
        'emoji': '💎',
        'category': 'subscription',
        'duration': 30,
        'effect': 'vip'
    },
    'trader_month': {
        'name': 'Трейдер PRO',
        'description': '30 дней: +15% к доходу',
        'price': 8000,
        'emoji': '📈',
        'category': 'subscription',
        'duration': 30,
        'effect': 'trader'
    },
    'investor_month': {
        'name': 'Инвестор',
        'description': '30 дней: +20% к доходу',
        'price': 12000,
        'emoji': '💰',
        'category': 'subscription',
        'duration': 30,
        'effect': 'investor'
    },
    
    # Спецпредложения
    'lucky_box': {
        'name': 'Лаки бокс',
        'description': 'Случайный предмет или деньги',
        'price': 300,
        'emoji': '🎁',
        'category': 'special',
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
        old = data['price']
        change = random.uniform(-0.1, 0.1)
        data['prev_price'] = old
        data['price'] = round(old * (1 + change), 2)
    save_companies(companies)

def get_price_change(old, new):
    if old == 0:
        return "0.00%"
    return f"{((new-old)/old)*100:+.2f}%"

def get_companies_page(page=1, per_page=10):
    items = list(load_companies().items())
    total = len(items)
    start = (page - 1) * per_page
    return items[start:start+per_page], total

# ========== ПОЛЬЗОВАТЕЛИ ==========
def get_user_file(user_id):
    return os.path.join(USERS_DIR, f"{user_id}.json")

def get_user(user_id):
    path = get_user_file(user_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            user = json.load(f)
            if 'inventory' not in user:
                user['inventory'] = []
            if 'cubes' not in user:
                user['cubes'] = 0
            if 'active_effects' not in user:
                user['active_effects'] = {}
            if 'shields' not in user:
                user['shields'] = 0
            if 'subscriptions' not in user:
                user['subscriptions'] = {}
            return user
    else:
        user = {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'username': None,
            'first_seen': str(datetime.now()),
            'last_seen': str(datetime.now()),
            'used_promos': [],
            'inventory': [],
            'cubes': 0,
            'active_effects': {},
            'shields': 0,
            'subscriptions': {}
        }
        save_user(user_id, user)
        return user

def save_user(user_id, data):
    with open(get_user_file(user_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_user_last_seen(user_id):
    user = get_user(user_id)
    user['last_seen'] = str(datetime.now())
    save_user(user_id, user)

def get_portfolio(user_id):
    user = get_user(user_id)
    companies = load_companies()
    return [{'ticker': t, 'amount': a, 'price': companies[t]['price'], 'name': companies[t]['name']}
            for t, a in user.get('portfolio', {}).items() if t in companies]

def calculate_capital(user_id):
    user = get_user(user_id)
    companies = load_companies()
    total = user['money']
    for t, a in user.get('portfolio', {}).items():
        if t in companies:
            total += a * companies[t]['price']
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
        user['portfolio'][ticker] = user['portfolio'].get(ticker, 0) + amount
        save_user(user_id, user)
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    return False, f"❌ Нужно ${total:,.2f}"

def sell_stock(user_id, ticker, amount):
    companies = load_companies()
    user = get_user(user_id)
    if ticker not in user['portfolio'] or user['portfolio'][ticker] < amount:
        return False, f"❌ У вас только {user['portfolio'].get(ticker,0)} акций"
    price = companies[ticker]['price']
    total = price * amount
    user['money'] += total
    user['money'] = round(user['money'], 2)
    user['portfolio'][ticker] -= amount
    if user['portfolio'][ticker] == 0:
        del user['portfolio'][ticker]
    save_user(user_id, user)
    return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"

def buy_item(user_id, item_id):
    user = get_user(user_id)
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return False, "❌ Товар не найден"
    if user['money'] < item['price']:
        return False, f"❌ Нужно ${item['price']}"
    user['money'] -= item['price']
    user['money'] = round(user['money'], 2)
    user['inventory'].append({
        'item_id': item_id,
        'name': item['name'],
        'emoji': item['emoji'],
        'description': item['description'],
        'category': item['category'],
        'effect': item.get('effect', 'none')
    })
    save_user(user_id, user)
    return True, f"✅ Куплен {item['emoji']} {item['name']}"

def activate_item(user_id, idx):
    user = get_user(user_id)
    if idx < 0 or idx >= len(user['inventory']):
        return False, "❌ Предмет не найден", None
    
    item = user['inventory'].pop(idx)
    effect_message = ""
    effect_data = None
    
    if item['effect'] == 'booster':
        user['active_effects']['booster'] = str(datetime.now() + timedelta(days=1))
        effect_message = "🚀 Ускоритель активирован! Цены будут расти на 50% быстрее в течение 24 часов."
        effect_data = {'type': 'booster', 'duration': '24 часа'}
        
    elif item['effect'] == 'shield':
        user['shields'] = user.get('shields', 0) + 1
        effect_message = "🛡️ Страховка активирована! Вы защищены от одного убытка."
        effect_data = {'type': 'shield', 'count': user['shields']}
        
    elif item['effect'] == 'analyst':
        companies = load_companies()
        predictions = []
        for ticker, data in list(companies.items())[:5]:
            trend = random.choice(['🚀 вырастет', '📉 упадет', '➡️ без изменений'])
            predictions.append(f"{ticker}: {trend}")
        effect_message = "📊 Аналитик: прогноз на завтра\n" + "\n".join(predictions)
        effect_data = {'type': 'analyst', 'predictions': predictions}
        
    elif item['effect'] == 'random':
        bonus = random.randint(50, 500)
        user['money'] += bonus
        effect_message = f"🎲 Случайный бонус: +${bonus}!"
        effect_data = {'type': 'random', 'bonus': bonus}
        
    elif item['effect'] in ['vip', 'trader', 'investor']:
        duration = 30
        if item['effect'] == 'vip':
            bonus = 10
        elif item['effect'] == 'trader':
            bonus = 15
        else:
            bonus = 20
            
        end_date = datetime.now() + timedelta(days=duration)
        user['subscriptions'][item['effect']] = {
            'end_date': str(end_date),
            'bonus': bonus
        }
        effect_message = f"{item['emoji']} Подписка {item['name']} активирована на {duration} дней! Бонус: +{bonus}% к доходу."
        effect_data = {'type': 'subscription', 'name': item['name'], 'duration': duration, 'bonus': bonus}
        
    elif item['effect'] == 'lucky_box':
        chance = random.random()
        if chance < 0.3:
            bonus = random.randint(100, 1000)
            user['money'] += bonus
            effect_message = f"🎁 Вам выпало: ${bonus}!"
            effect_data = {'type': 'money', 'amount': bonus}
        elif chance < 0.6:
            random_items = ['booster', 'shield', 'analyst']
            random_item = random.choice(random_items)
            user['inventory'].append({
                'item_id': random_item,
                'name': SHOP_ITEMS[random_item]['name'],
                'emoji': SHOP_ITEMS[random_item]['emoji'],
                'description': SHOP_ITEMS[random_item]['description'],
                'category': SHOP_ITEMS[random_item]['category'],
                'effect': SHOP_ITEMS[random_item]['effect']
            })
            effect_message = f"🎁 Вам выпал предмет: {SHOP_ITEMS[random_item]['emoji']} {SHOP_ITEMS[random_item]['name']}!"
            effect_data = {'type': 'item', 'item': random_item}
        else:
            effect_message = "🎁 Вам ничего не выпало... Повезет в следующий раз!"
            effect_data = {'type': 'nothing'}
    
    save_user(user_id, user)
    return True, effect_message, effect_data

# ========== ЛИДЕРЫ ==========
def update_leaderboard():
    lb = []
    for f in os.listdir(USERS_DIR):
        if f.endswith('.json'):
            uid = int(f[:-5])
            user = get_user(uid)
            cap = calculate_capital(uid)
            lb.append({
                'user_id': uid,
                'username': user.get('username', f"User_{uid}"),
                'capital': cap,
                'cubes': user.get('cubes', 0)
            })
    lb.sort(key=lambda x: x['capital'], reverse=True)
    save_json(LEADERBOARD_FILE, lb)
    return lb

def get_leaderboard(limit=10):
    lb = load_json(LEADERBOARD_FILE)
    if not lb:
        lb = update_leaderboard()
    return lb[:limit]

# ========== ПРОМОКОДЫ ==========
def load_promocodes():
    p = load_json(PROMOCODES_FILE)
    if not p:
        p = DEFAULT_PROMOCODES.copy()
        save_json(PROMOCODES_FILE, p)
    return p

def save_promocodes(p):
    save_json(PROMOCODES_FILE, p)

def get_promocode(code):
    return load_promocodes().get(code.upper())

def add_promocode(code, bonus, max_uses):
    p = load_promocodes()
    if code.upper() in p:
        return False
    p[code.upper()] = {'bonus': bonus, 'max_uses': max_uses, 'used_count': 0}
    save_promocodes(p)
    return True

def delete_promocode(code):
    p = load_promocodes()
    if code in p:
        del p[code]
        save_promocodes(p)
        return True
    return False

def use_promo(user_id, code):
    p = load_promocodes()
    code = code.upper()
    if code not in p:
        return False, "❌ Промокод не найден"
    promo = p[code]
    if promo['used_count'] >= promo['max_uses']:
        return False, "❌ Промокод закончился"
    user = get_user(user_id)
    if code in user.get('used_promos', []):
        return False, "❌ Уже активирован"
    user['money'] += promo['bonus']
    user['used_promos'] = user.get('used_promos', []) + [code]
    save_user(user_id, user)
    promo['used_count'] += 1
    save_promocodes(p)
    return True, f"✅ +${promo['bonus']}"

# ========== СЕЗОН ==========
def get_current_season():
    s = load_json(SEASON_FILE)
    if not s:
        s = DEFAULT_SEASON.copy()
        save_json(SEASON_FILE, s)
    return s

def create_season(name, days):
    s = {
        'name': name,
        'start': str(datetime.now()),
        'end': str(datetime.now() + timedelta(days=days)),
        'active': True
    }
    save_json(SEASON_FILE, s)

def end_season():
    s = get_current_season()
    if not s['active']:
        return False, "❌ Уже завершён"
    s['active'] = False
    save_json(SEASON_FILE, s)
    top = get_leaderboard(3)
    for i, e in enumerate(top, 1):
        u = get_user(e['user_id'])
        u['cubes'] = u.get('cubes', 0) + 1
        u['inventory'].append({
            'item_id': 'cube',
            'name': f'{s["name"]} Кубок {i}',
            'emoji': '🏆',
            'description': f'Награда за {i} место',
            'effect': 'cube'
        })
        save_user(e['user_id'], u)
    return True, "✅ Сезон завершён"

def get_season_time_left():
    s = get_current_season()
    if not s['active']:
        return None, None
    end = datetime.fromisoformat(s['end'])
    now = datetime.now()
    if now > end:
        end_season()
        return None, None
    return (end - now).days, ((end - now).seconds // 3600)

# ========== КНОПКИ ==========
def main_menu_kb():
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

def back_kb(target):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data=target))
    return markup

def shop_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📦 РАСХОДНИКИ", callback_data="shop_category_consumable"),
        types.InlineKeyboardButton("💎 ПОДПИСКИ", callback_data="shop_category_subscription"),
        types.InlineKeyboardButton("🎁 СПЕЦПРЕДЛОЖЕНИЯ", callback_data="shop_category_special"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup

def shop_category_kb(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item_id, item in SHOP_ITEMS.items():
        if item['category'] == category:
            markup.add(types.InlineKeyboardButton(
                f"{item['emoji']} {item['name']} — ${item['price']}",
                callback_data=f"shop_item_{item_id}"
            ))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="shop"))
    return markup

def inventory_kb(user):
    markup = types.InlineKeyboardMarkup(row_width=1)
    inventory = user.get('inventory', [])
    if inventory:
        for i, item in enumerate(inventory):
            markup.add(types.InlineKeyboardButton(
                f"{item['emoji']} {item['name']}",
                callback_data=f"inv_item_{i}"
            ))
    else:
        markup.add(types.InlineKeyboardButton("😢 Инвентарь пуст", callback_data="noop"))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
    return markup

def companies_kb(page, total_pages):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(types.InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
        else:
            row.append(types.InlineKeyboardButton("◀️", callback_data="noop"))
            
        row.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            row.append(types.InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
        else:
            row.append(types.InlineKeyboardButton("▶️", callback_data="noop"))
            
        markup.row(*row)
    
    markup.row(
        types.InlineKeyboardButton("🏠 Главная", callback_data="back_to_main"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_companies")
    )
    return markup

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start', 'trade'])
def start_cmd(message):
    uid = message.from_user.id
    name = message.from_user.username or message.from_user.first_name or f"User_{uid}"
    user = get_user(uid)
    user['username'] = name
    user['last_seen'] = str(datetime.now())
    save_user(uid, user)
    
    season = get_current_season()
    d, h = get_season_time_left()
    time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}"
    
    if IMAGES.get('main'):
        bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "📚 *Помощь по игре*\n\n"
        "*Команды:*\n"
        "/start - начать игру\n"
        "/help - эта помощь\n"
        "/tbuy КОМПАНИЯ КОЛ-ВО - купить акции\n"
        "/tsell КОМПАНИЯ КОЛ-ВО - продать акции\n"
        "/tnext - следующий день\n"
        "/tstats - твоя статистика\n"
        "/tlist - список компаний\n"
        "/tleader - таблица лидеров\n"
        "/tpromo КОД - активировать промокод\n"
        "/promo - список промокодов\n"
        "/shop - магазин\n"
        "/inventory - инвентарь\n\n"
        "*Предметы:*\n"
        "🚀 Ускоритель - цены растут быстрее 24ч\n"
        "🛡️ Страховка - защита от 1 убытка\n"
        "📊 Аналитик - прогноз цен\n"
        "🎲 Рандом - случайный бонус\n"
        "💎 VIP - +10% к доходу 30 дней\n"
        "📈 Трейдер PRO - +15% к доходу 30 дней\n"
        "💰 Инвестор - +20% к доходу 30 дней\n"
        "🎁 Лаки бокс - случайный приз"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tbuy'])
def buy_stock_cmd(m):
    try:
        _, ticker, am = m.text.split()
        ticker = ticker.upper()
        am = int(am)
        ok, msg = buy_stock(m.from_user.id, ticker, am)
        bot.reply_to(m, msg)
        if ok:
            update_user_last_seen(m.from_user.id)
    except:
        bot.reply_to(m, "❌ Формат: /tbuy AAPL 5")

@bot.message_handler(commands=['tsell'])
def sell_stock_cmd(m):
    try:
        _, ticker, am = m.text.split()
        ticker = ticker.upper()
        am = int(am)
        ok, msg = sell_stock(m.from_user.id, ticker, am)
        bot.reply_to(m, msg)
        if ok:
            update_user_last_seen(m.from_user.id)
    except:
        bot.reply_to(m, "❌ Формат: /tsell AAPL 5")

@bot.message_handler(commands=['tnext'])
def next_cmd(m):
    uid = m.from_user.id
    update_company_prices()
    user = get_user(uid)
    user['day'] += 1
    user['last_seen'] = str(datetime.now())
    save_user(uid, user)
    update_leaderboard()
    
    season = get_current_season()
    d, h = get_season_time_left()
    time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}"
    
    if IMAGES.get('main'):
        bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=['tpromo'])
def promo_activate_cmd(m):
    try:
        code = m.text.split()[1].upper()
        promo = get_promocode(code)
        if promo:
            remaining = promo['max_uses'] - promo['used_count']
            text = f"🎟️ Промокод: {code}\n💰 +${promo['bonus']}\n🎫 Осталось: {remaining}"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Активировать", callback_data=f"confirm_promo_{code}"),
                types.InlineKeyboardButton("❌ Отмена", callback_data="back_to_main")
            )
            if IMAGES.get('main'):
                bot.send_photo(m.chat.id, IMAGES['main'], caption=text, reply_markup=markup)
            else:
                bot.send_message(m.chat.id, text, reply_markup=markup)
        else:
            bot.reply_to(m, "❌ Промокод не найден")
    except:
        bot.reply_to(m, "❌ Использование: /tpromo КОД")

@bot.message_handler(commands=['tlist'])
def list_cmd(m):
    uid = m.from_user.id
    user = get_user(uid)
    items, total = get_companies_page(1)
    pages = (total + 9) // 10
    
    text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
    for ticker, data in items:
        change = get_price_change(data.get('prev_price', data['price']), data['price'])
        emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
        text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f} {emoji} {change}\n\n"
    
    if IMAGES.get('companies'):
        bot.send_photo(uid, IMAGES['companies'], caption=text, reply_markup=companies_kb(1, pages))
    else:
        bot.send_message(uid, text, reply_markup=companies_kb(1, pages))

@bot.message_handler(commands=['tstats'])
def stats_cmd(m):
    uid = m.from_user.id
    user = get_user(uid)
    cap = calculate_capital(uid)
    port = get_portfolio(uid)
    
    text = f"📊 ТВОЯ СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n💵 Капитал: ${cap:,.2f}\n🏆 Кубков: {user.get('cubes',0)}\n"
    
    if user.get('active_effects'):
        text += "\n✨ *Активные эффекты:*\n"
        if 'booster' in user['active_effects']:
            text += "🚀 Ускоритель активен\n"
    
    if user.get('shields', 0) > 0:
        text += f"🛡️ Страховок: {user['shields']}\n"
    
    if user.get('subscriptions'):
        text += "\n💎 *Подписки:*\n"
        for sub, data in user['subscriptions'].items():
            text += f"• +{data['bonus']}% до {data['end_date'][:10]}\n"
    
    text += "\n📋 *Портфель:*\n"
    if port:
        for p in port:
            text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
    else:
        text += "Пусто\n"
    
    lb = get_leaderboard(50)
    for i, e in enumerate(lb, 1):
        if e['user_id'] == uid:
            text += f"\n⭐ Место: {i} из {len(lb)}"
            break
    
    if IMAGES.get('stats'):
        bot.send_photo(uid, IMAGES['stats'], caption=text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tleader'])
def leader_cmd(m):
    lb = get_leaderboard(10)
    text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
    
    for i, e in enumerate(lb, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
    
    if IMAGES.get('leaderboard'):
        bot.send_photo(m.chat.id, IMAGES['leaderboard'], caption=text, reply_markup=back_kb("back_to_main"))
    else:
        bot.send_message(m.chat.id, text, reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['inventory'])
def inventory_cmd(m):
    uid = m.from_user.id
    user = get_user(uid)
    
    text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
    if user.get('inventory'):
        for i, item in enumerate(user['inventory'], 1):
            text += f"{i}. {item['emoji']} {item['name']}\n"
    else:
        text += "Пусто\n"
    text += f"\n🏆 Кубков: {user.get('cubes',0)}"
    
    if IMAGES.get('inventory'):
        bot.send_photo(uid, IMAGES['inventory'], caption=text, reply_markup=inventory_kb(user))
    else:
        bot.send_message(uid, text, reply_markup=inventory_kb(user))

@bot.message_handler(commands=['shop'])
def shop_cmd(m):
    text = "🛒 МАГАЗИН\n\nВыбери категорию:"
    if IMAGES.get('shop'):
        bot.send_photo(m.chat.id, IMAGES['shop'], caption=text, reply_markup=shop_kb())
    else:
        bot.send_message(m.chat.id, text, reply_markup=shop_kb())

@bot.message_handler(commands=['promo'])
def promo_list_cmd(m):
    promos = load_promocodes()
    text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
    for code, d in promos.items():
        rem = d['max_uses'] - d['used_count']
        text += f"`{code}` — +${d['bonus']} (осталось {rem}/{d['max_uses']})\n"
    text += "\nАктивировать: /tpromo КОД"
    
    if IMAGES.get('main'):
        bot.send_photo(m.chat.id, IMAGES['main'], caption=text, reply_markup=back_kb("back_to_main"))
    else:
        bot.send_message(m.chat.id, text, reply_markup=back_kb("back_to_main"))

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data
    
    try:
        # ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ =====
        if data == "back_to_main":
            user = get_user(uid)
            season = get_current_season()
            d, h = get_season_time_left()
            time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}"
            
            if call.message.photo:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=main_menu_kb()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_menu_kb()
                )
            bot.answer_callback_query(call.id)
            return

        # ===== СТАТУС =====
        if data == "status":
            user = get_user(uid)
            cap = calculate_capital(uid)
            port = get_portfolio(uid)
            
            text = f"📊 ТВОЯ СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n💵 Капитал: ${cap:,.2f}\n🏆 Кубков: {user.get('cubes',0)}\n"
            
            if user.get('active_effects'):
                text += "\n✨ *Активные эффекты:*\n"
                if 'booster' in user['active_effects']:
                    text += "🚀 Ускоритель активен\n"
            
            if user.get('shields', 0) > 0:
                text += f"🛡️ Страховок: {user['shields']}\n"
            
            if user.get('subscriptions'):
                text += "\n💎 *Подписки:*\n"
                for sub, data in user['subscriptions'].items():
                    text += f"• +{data['bonus']}% до {data['end_date'][:10]}\n"
            
            text += "\n📋 *Портфель:*\n"
            if port:
                for p in port:
                    text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
            else:
                text += "Пусто\n"
            
            lb = get_leaderboard(50)
            for i, e in enumerate(lb, 1):
                if e['user_id'] == uid:
                    text += f"\n⭐ Место: {i} из {len(lb)}"
                    break
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['stats'], caption=text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=back_kb("back_to_main")
                )
            bot.answer_callback_query(call.id)
            return

        # ===== КОМПАНИИ =====
        if data == "list":
            user = get_user(uid)
            items, total = get_companies_page(1)
            pages = (total + 9) // 10
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for ticker, data in items:
                change = get_price_change(data.get('prev_price', data['price']), data['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f} {emoji} {change}\n\n"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['companies'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=companies_kb(1, pages)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=companies_kb(1, pages)
                )
            bot.answer_callback_query(call.id)
            return

        # ===== NEXT =====
        if data == "next":
            update_company_prices()
            user = get_user(uid)
            user['day'] += 1
            user['last_seen'] = str(datetime.now())
            save_user(uid, user)
            update_leaderboard()
            
            season = get_current_season()
            d, h = get_season_time_left()
            time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=main_menu_kb()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_menu_kb()
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ЛИДЕРЫ =====
        if data == "leaderboard":
            lb = get_leaderboard(10)
            text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
            
            for i, e in enumerate(lb, 1):
                medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
                text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['leaderboard'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            bot.answer_callback_query(call.id)
            return

        # ===== МАГАЗИН =====
        if data == "shop":
            text = "🛒 МАГАЗИН\n\nВыбери категорию:"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['shop'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=shop_kb()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=shop_kb()
                )
            bot.answer_callback_query(call.id)
            return

        # ===== КАТЕГОРИИ МАГАЗИНА =====
        if data.startswith("shop_category_"):
            category = data.replace("shop_category_", "")
            category_names = {
                'consumable': '📦 РАСХОДНИКИ',
                'subscription': '💎 ПОДПИСКИ',
                'special': '🎁 СПЕЦПРЕДЛОЖЕНИЯ'
            }
            
            text = f"{category_names.get(category, 'ТОВАРЫ')}\n\nВыбери товар:"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['shop'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=shop_category_kb(category)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=shop_category_kb(category)
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ТОВАР В МАГАЗИНЕ =====
        if data.startswith("shop_item_"):
            item_id = data[10:]
            item = SHOP_ITEMS.get(item_id)
            
            if not item:
                bot.answer_callback_query(call.id, "❌ Товар не найден")
                return
            
            user = get_user(uid)
            text = f"{item['emoji']} *{item['name']}*\n\n{item['description']}\n\n💰 Цена: ${item['price']}\n💳 Твой баланс: ${user['money']:,.2f}\n\nКупить?"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Купить", callback_data=f"buy_item_{item_id}"),
                types.InlineKeyboardButton("◀️ Назад", callback_data=f"shop_category_{item['category']}")
            )
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['shop'], caption=text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ПОКУПКА ПРЕДМЕТА =====
        if data.startswith("buy_item_"):
            item_id = data[9:]
            ok, msg = buy_item(uid, item_id)
            
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
            if ok:
                update_user_last_seen(uid)
                
                item = SHOP_ITEMS.get(item_id)
                if item:
                    category = item['category']
                    category_names = {
                        'consumable': '📦 РАСХОДНИКИ',
                        'subscription': '💎 ПОДПИСКИ',
                        'special': '🎁 СПЕЦПРЕДЛОЖЕНИЯ'
                    }
                    
                    text = f"{category_names.get(category, 'ТОВАРЫ')}\n\nВыбери товар:"
                    
                    if call.message.photo:
                        bot.edit_message_media(
                            types.InputMediaPhoto(IMAGES['shop'], caption=text),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=shop_category_kb(category)
                        )
                    else:
                        bot.edit_message_text(
                            text,
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=shop_category_kb(category)
                        )
            return

        # ===== ИНВЕНТАРЬ =====
        if data == "inventory":
            user = get_user(uid)
            
            text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
            if user.get('inventory'):
                for i, item in enumerate(user['inventory'], 1):
                    text += f"{i}. {item['emoji']} {item['name']}\n"
            else:
                text += "Пусто\n"
            text += f"\n🏆 Кубков: {user.get('cubes',0)}"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['inventory'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=inventory_kb(user)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=inventory_kb(user)
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ПРЕДМЕТ В ИНВЕНТАРЕ =====
        if data.startswith("inv_item_"):
            idx = int(data[9:])
            user = get_user(uid)
            
            if idx >= len(user.get('inventory', [])):
                bot.answer_callback_query(call.id, "❌ Предмет не найден")
                return
            
            item = user['inventory'][idx]
            text = f"{item['emoji']} *{item['name']}*\n\n{item.get('description', '')}\n\nАктивировать?"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Активировать", callback_data=f"use_item_{idx}"),
                types.InlineKeyboardButton("◀️ Назад", callback_data="inventory")
            )
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['inventory'], caption=text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ИСПОЛЬЗОВАНИЕ ПРЕДМЕТА =====
        if data.startswith("use_item_"):
            idx = int(data[9:])
            ok, msg, effect_data = activate_item(uid, idx)
            
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
            if ok:
                update_user_last_seen(uid)
                
                user = get_user(uid)
                text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
                if user.get('inventory'):
                    for i, item in enumerate(user['inventory'], 1):
                        text += f"{i}. {item['emoji']} {item['name']}\n"
                else:
                    text += "Пусто\n"
                text += f"\n🏆 Кубков: {user.get('cubes',0)}"
                
                if call.message.photo:
                    bot.edit_message_media(
                        types.InputMediaPhoto(IMAGES['inventory'], caption=text),
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=inventory_kb(user)
                    )
                else:
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=inventory_kb(user)
                    )
            return

        # ===== ПРОМО =====
        if data == "promo":
            promos = load_promocodes()
            text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
            for code, d in promos.items():
                rem = d['max_uses'] - d['used_count']
                text += f"`{code}` — +${d['bonus']} (осталось {rem}/{d['max_uses']})\n"
            text += "\nАктивировать: /tpromo КОД"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ПОМОЩЬ =====
        if data == "help":
            help_text = (
                "📚 *Помощь по игре*\n\n"
                "*Команды:*\n"
                "/start - начать игру\n"
                "/help - эта помощь\n"
                "/tbuy КОМПАНИЯ КОЛ-ВО - купить акции\n"
                "/tsell КОМПАНИЯ КОЛ-ВО - продать акции\n"
                "/tnext - следующий день\n"
                "/tstats - твоя статистика\n"
                "/tlist - список компаний\n"
                "/tleader - таблица лидеров\n"
                "/tpromo КОД - активировать промокод\n"
                "/promo - список промокодов\n"
                "/shop - магазин\n"
                "/inventory - инвентарь\n\n"
                "*Предметы:*\n"
                "🚀 Ускоритель - цены растут быстрее 24ч\n"
                "🛡️ Страховка - защита от 1 убытка\n"
                "📊 Аналитик - прогноз цен\n"
                "🎲 Рандом - случайный бонус\n"
                "💎 VIP - +10% к доходу 30 дней\n"
                "📈 Трейдер PRO - +15% к доходу 30 дней\n"
                "💰 Инвестор - +20% к доходу 30 дней\n"
                "🎁 Лаки бокс - случайный приз"
            )
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=help_text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=back_kb("back_to_main")
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=back_kb("back_to_main")
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ПАГИНАЦИЯ КОМПАНИЙ =====
        if data.startswith("page_"):
            page = int(data[5:])
            user = get_user(uid)
            items, total = get_companies_page(page)
            pages = (total + 9) // 10
            
            if page < 1 or page > pages:
                bot.answer_callback_query(call.id, "Нет страниц")
                return
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for ticker, data in items:
                change = get_price_change(data.get('prev_price', data['price']), data['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f} {emoji} {change}\n\n"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['companies'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=companies_kb(page, pages)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=companies_kb(page, pages)
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ОБНОВЛЕНИЕ КОМПАНИЙ =====
        if data == "refresh_companies":
            user = get_user(uid)
            items, total = get_companies_page(1)
            pages = (total + 9) // 10
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for ticker, data in items:
                change = get_price_change(data.get('prev_price', data['price']), data['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f} {emoji} {change}\n\n"
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['companies'], caption=text),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=companies_kb(1, pages)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=companies_kb(1, pages)
                )
            bot.answer_callback_query(call.id, "🔄 Цены обновлены")
            return

        # ===== ПОДТВЕРЖДЕНИЕ ПРОМОКОДА =====
        if data.startswith("confirm_promo_"):
            code = data[14:]
            ok, msg = use_promo(uid, code)
            
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
            if ok:
                update_user_last_seen(uid)
                
                user = get_user(uid)
                season = get_current_season()
                d, h = get_season_time_left()
                time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
                
                text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}"
                
                if call.message.photo:
                    bot.edit_message_media(
                        types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=main_menu_kb()
                    )
                else:
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="Markdown",
                        reply_markup=main_menu_kb()
                    )
            return

        # ===== NOOP =====
        if data == "noop":
            bot.answer_callback_query(call.id)
            return

    except Exception as e:
        print(f"[ERROR] {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['adminhelp'])
def admin_help(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.reply_to(m, "/admingive ID сумма\n/admintake ID сумма\n/adminreset ID\n/adminpromo КОД БОНУС МАКС\n/adminpromodel КОД\n/adminpromos\n/admincomps\n/adminseason НАЗВАНИЕ ДНЕЙ\n/adminseasonend\n/adminstats\n/admintop\n/addleader - обновить таблицу лидеров")

@bot.message_handler(commands=['admingive'])
def admin_give(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, tid, am = m.text.split()
        tid = int(tid)
        am = float(am)
        user = get_user(tid)
        user['money'] += am
        save_user(tid, user)
        update_leaderboard()
        bot.reply_to(m, f"✅ Выдано ${am:,.2f}")
    except:
        bot.reply_to(m, "❌ /admingive ID СУММА")

@bot.message_handler(commands=['admintake'])
def admin_take(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, tid, am = m.text.split()
        tid = int(tid)
        am = float(am)
        user = get_user(tid)
        user['money'] = max(0, user['money'] - am)
        save_user(tid, user)
        update_leaderboard()
        bot.reply_to(m, f"✅ Забрано ${am:,.2f}")
    except:
        bot.reply_to(m, "❌ /admintake ID СУММА")

@bot.message_handler(commands=['adminreset'])
def admin_reset(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        tid = int(m.text.split()[1])
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
            'active_effects': {},
            'shields': 0,
            'subscriptions': {}
        }
        save_user(tid, user_data)
        update_leaderboard()
        bot.reply_to(m, f"✅ Пользователь {tid} сброшен")
    except:
        bot.reply_to(m, "❌ /adminreset ID")

@bot.message_handler(commands=['adminpromo'])
def admin_promo_add(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, code, bonus, mu = m.text.split()
        if add_promocode(code, int(bonus), int(mu)):
            bot.reply_to(m, f"✅ Промокод {code} добавлен")
        else:
            bot.reply_to(m, "❌ Уже существует")
    except:
        bot.reply_to(m, "❌ /adminpromo КОД БОНУС МАКС")

@bot.message_handler(commands=['adminpromodel'])
def admin_promo_del(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        code = m.text.split()[1].upper()
        if delete_promocode(code):
            bot.reply_to(m, f"✅ Промокод {code} удалён")
        else:
            bot.reply_to(m, "❌ Не найден")
    except:
        bot.reply_to(m, "❌ /adminpromodel КОД")

@bot.message_handler(commands=['adminpromos'])
def admin_promos_list(m):
    if m.from_user.id != ADMIN_ID:
        return
    p = load_promocodes()
    text = "🎟️ ПРОМОКОДЫ:\n"
    for code, d in p.items():
        text += f"{code} — ${d['bonus']} — {d['used_count']}/{d['max_uses']}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['admincomps'])
def admin_comps_list(m):
    if m.from_user.id != ADMIN_ID:
        return
    c = load_companies()
    text = "📋 КОМПАНИИ:\n"
    for t, d in c.items():
        text += f"{t} — {d['name']} — ${d['price']:,.2f}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['adminseason'])
def admin_season_create(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, name, days = m.text.split()
        create_season(name, int(days))
        bot.reply_to(m, f"✅ Сезон '{name}' на {days} дней")
    except:
        bot.reply_to(m, "❌ /adminseason НАЗВАНИЕ ДНЕЙ")

@bot.message_handler(commands=['adminseasonend'])
def admin_season_end(m):
    if m.from_user.id != ADMIN_ID:
        return
    ok, msg = end_season()
    bot.reply_to(m, msg)

@bot.message_handler(commands=['adminstats'])
def admin_stats(m):
    if m.from_user.id != ADMIN_ID:
        return
    total_users = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
    total_money = sum(get_user(int(f[:-5]))['money'] for f in os.listdir(USERS_DIR) if f.endswith('.json'))
    promos = load_promocodes()
    total_promos = len(promos)
    total_acts = sum(p['used_count'] for p in promos.values())
    companies = load_companies()
    bot.reply_to(m, f"📊 ИГРОКОВ: {total_users}\n💰 ДЕНЕГ: ${total_money:,.2f}\n🎟️ ПРОМОКОДОВ: {total_promos}\n🎫 АКТИВАЦИЙ: {total_acts}\n🏢 КОМПАНИЙ: {len(companies)}")

@bot.message_handler(commands=['admintop'])
def admin_top(m):
    if m.from_user.id != ADMIN_ID:
        return
    top = get_leaderboard(10)
    text = "🏆 ТОП-10:\n"
    for i, e in enumerate(top, 1):
        text += f"{i}. {e['username']} — ${e['capital']:,.2f}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['addleader'])
def admin_update_leaderboard(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        update_leaderboard()
        bot.reply_to(m, "✅ Таблица лидеров обновлена!")
    except Exception as e:
        bot.reply_to(m, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен")
    print("✅ Сообщения РЕДАКТИРУЮТСЯ, новые НЕ создаются")
    print("✅ Фото есть ВЕЗДЕ")
    print("✅ Работает как в старых версиях")
    bot.infinity_polling()