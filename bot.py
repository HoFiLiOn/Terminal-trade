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
SETTINGS_FILE = "settings.json"
BANNED_USERS_FILE = "banned_users.json"

# Создаем папки
if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== НАСТРОЙКИ ==========
DEFAULT_SETTINGS = {
    'start_money': 1000.0,
    'price_change_min': -0.1,
    'price_change_max': 0.1,
    'random_bonus_min': 50,
    'random_bonus_max': 500,
    'lucky_box_money_min': 100,
    'lucky_box_money_max': 1000,
    'vip_bonus': 10,
    'trader_bonus': 15,
    'investor_bonus': 20
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_setting(key):
    return load_settings().get(key, DEFAULT_SETTINGS.get(key))

def update_setting(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)

# ========== БАНЫ ==========
def load_banned():
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_banned(banned):
    with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned, f, indent=2, ensure_ascii=False)

def is_banned(user_id):
    return str(user_id) in load_banned()

def ban_user(user_id):
    banned = load_banned()
    banned[str(user_id)] = str(datetime.now())
    save_banned(banned)

def unban_user(user_id):
    banned = load_banned()
    if str(user_id) in banned:
        del banned[str(user_id)]
        save_banned(banned)

# ========== ТЕКСТЫ ==========
STORY_TEXT = """📜 *Небольшая предыстория...*

Ты обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота.
В описании было сказано: *«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»*.

Сначала ты подумал, что это очередной развод, но любопытство взяло верх.
Ты запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.

Теперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.

Добро пожаловать в *Terminal Trade*."""

HELP_TEXT = """📚 *Помощь по игре*

*Команды:*
/start - начать игру
/help - эта помощь
/tbuy КОМПАНИЯ КОЛ-ВО - купить акции
/tsell КОМПАНИЯ КОЛ-ВО - продать акции
/tnext - следующий день
/tstats - твоя статистика
/tlist - список компаний
/tleader - таблица лидеров
/tpromo КОД - активировать промокод
/promo - список промокодов
/shop - магазин
/inventory - инвентарь
/admin - админ-панель (только для админа)

*Предметы:*
🚀 Ускоритель - цены растут быстрее 24ч
🛡️ Страховка - защита от 1 убытка
📊 Аналитик - прогноз цен
🎲 Рандом - случайный бонус
💎 VIP - +10% к доходу 30 дней
📈 Трейдер PRO - +15% к доходу 30 дней
💰 Инвестор - +20% к доходу 30 дней
🎁 Лаки бокс - случайный приз"""

# ========== КАРТИНКИ ==========
IMAGES = {
    'main': 'https://s10.iimage.su/s/05/gIKluIYxLgUpL28XWRh1IzTmdY4DzqMQuX8v39ee9.jpg',
    'companies': 'https://s10.iimage.su/s/05/gf3a1gxxMZn6ArfLKZD3JlzVhy83Bm1cGvNVjC0vI.jpg',
    'stats': 'https://s10.iimage.su/s/05/gioJHlUxz7G3Udtvbpc4t3CAoCSsryhLnSFXWdayc.jpg',
    'inventory': 'https://s10.iimage.su/s/05/grMXdR3xwFaLXdQ74TR9rz7zu8Wb60ezeX89JKuzm.jpg',
    'shop': 'https://s10.iimage.su/s/05/gbuaUsrxIjSjwQcGwcZrUaNcbFXzpITC2qFzhFzrd.jpg',
    'leaderboard': 'https://s10.iimage.su/s/05/gYoBW3cxowvFLbKdb8GJCDKWoEAcQD5DJa0zHCQt6.jpg'
}

# ========== КОМПАНИИ ==========
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

def load_companies():
    if os.path.exists(COMPANIES_FILE):
        with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_COMPANIES.copy()

def save_companies(companies):
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

def update_prices():
    companies = load_companies()
    settings = load_settings()
    change_min = settings.get('price_change_min', -0.1)
    change_max = settings.get('price_change_max', 0.1)
    
    for ticker, data in companies.items():
        old = data['price']
        change = random.uniform(change_min, change_max)
        data['prev_price'] = old
        data['price'] = round(old * (1 + change), 2)
    save_companies(companies)

def get_price_change(old, new):
    if old == 0:
        return "0.00%"
    return f"{((new-old)/old)*100:+.2f}%"

# ========== ПОЛЬЗОВАТЕЛИ ==========
def get_user(user_id):
    path = os.path.join(USERS_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            user = json.load(f)
            user.setdefault('inventory', [])
            user.setdefault('cubes', 0)
            user.setdefault('active_effects', {})
            user.setdefault('shields', 0)
            user.setdefault('subscriptions', {})
            user.setdefault('used_promos', [])
            user.setdefault('portfolio', {})
            return user
    else:
        settings = load_settings()
        user = {
            'money': settings.get('start_money', 1000.0),
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
    with open(os.path.join(USERS_DIR, f"{user_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def calculate_capital(user_id):
    user = get_user(user_id)
    companies = load_companies()
    total = user['money']
    for ticker, amount in user.get('portfolio', {}).items():
        if ticker in companies:
            total += amount * companies[ticker]['price']
    return round(total, 2)

def update_leaderboard():
    lb = []
    for f in os.listdir(USERS_DIR):
        if f.endswith('.json'):
            uid = int(f[:-5])
            if is_banned(uid):
                continue
            user = get_user(uid)
            cap = calculate_capital(uid)
            lb.append({
                'user_id': uid,
                'username': user.get('username', f"User_{uid}"),
                'capital': cap,
                'cubes': user.get('cubes', 0)
            })
    lb.sort(key=lambda x: x['capital'], reverse=True)
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(lb, f, indent=2, ensure_ascii=False)
    return lb

def get_leaderboard(limit=10):
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            lb = json.load(f)
            return lb[:limit]
    return update_leaderboard()[:limit]

# ========== ТОВАРЫ МАГАЗИНА ==========
SHOP_ITEMS = {
    'booster': {'name': 'Ускоритель', 'description': 'Цены будут расти на 50% быстрее 1 день', 'price': 500, 'emoji': '🚀', 'category': 'consumable', 'effect': 'booster'},
    'shield': {'name': 'Страховка', 'description': 'Защита от 1 убытка', 'price': 300, 'emoji': '🛡️', 'category': 'consumable', 'effect': 'shield'},
    'analyst': {'name': 'Аналитик', 'description': 'Прогноз цены на следующий день', 'price': 200, 'emoji': '📊', 'category': 'consumable', 'effect': 'analyst'},
    'random': {'name': 'Рандом', 'description': 'Случайный бонус от $50 до $500', 'price': 100, 'emoji': '🎲', 'category': 'consumable', 'effect': 'random'},
    'vip_month': {'name': 'VIP на месяц', 'description': '30 дней: +10% к доходу', 'price': 5000, 'emoji': '💎', 'category': 'subscription', 'duration': 30, 'effect': 'vip'},
    'trader_month': {'name': 'Трейдер PRO', 'description': '30 дней: +15% к доходу', 'price': 8000, 'emoji': '📈', 'category': 'subscription', 'duration': 30, 'effect': 'trader'},
    'investor_month': {'name': 'Инвестор', 'description': '30 дней: +20% к доходу', 'price': 12000, 'emoji': '💰', 'category': 'subscription', 'duration': 30, 'effect': 'investor'},
    'lucky_box': {'name': 'Лаки бокс', 'description': 'Случайный предмет или деньги', 'price': 300, 'emoji': '🎁', 'category': 'special', 'effect': 'lucky_box'}
}

def buy_item(user_id, item_id):
    user = get_user(user_id)
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return False, "❌ Товар не найден"
    if user['money'] < item['price']:
        return False, f"❌ Нужно ${item['price']}"
    user['money'] -= item['price']
    user['inventory'].append({
        'item_id': item_id,
        'name': item['name'],
        'emoji': item['emoji'],
        'description': item['description'],
        'category': item['category'],
        'effect': item.get('effect', 'none')
    })
    save_user(user_id, user)
    update_leaderboard()
    return True, f"✅ Куплен {item['emoji']} {item['name']}"

def use_item(user_id, idx):
    user = get_user(user_id)
    if idx < 0 or idx >= len(user['inventory']):
        return False, "❌ Предмет не найден", None
    
    item = user['inventory'].pop(idx)
    settings = load_settings()
    msg = ""
    data = None
    
    if item['effect'] == 'booster':
        user['active_effects']['booster'] = str(datetime.now() + timedelta(days=1))
        msg = "🚀 Ускоритель активирован!"
    elif item['effect'] == 'shield':
        user['shields'] = user.get('shields', 0) + 1
        msg = "🛡️ Страховка активирована!"
    elif item['effect'] == 'analyst':
        companies = load_companies()
        pred = []
        for t, d in list(companies.items())[:5]:
            trend = random.choice(['🚀 вырастет', '📉 упадет', '➡️ без изменений'])
            pred.append(f"{t}: {trend}")
        msg = "📊 Прогноз:\n" + "\n".join(pred)
    elif item['effect'] == 'random':
        bonus = random.randint(settings.get('random_bonus_min', 50), settings.get('random_bonus_max', 500))
        user['money'] += bonus
        msg = f"🎲 +${bonus}!"
    elif item['effect'] in ['vip', 'trader', 'investor']:
        bonus_map = {'vip': settings.get('vip_bonus', 10), 'trader': settings.get('trader_bonus', 15), 'investor': settings.get('investor_bonus', 20)}
        bonus = bonus_map.get(item['effect'], 10)
        end = datetime.now() + timedelta(days=30)
        user['subscriptions'][item['effect']] = {'end_date': str(end), 'bonus': bonus}
        msg = f"{item['emoji']} Подписка активирована! +{bonus}%"
    elif item['effect'] == 'lucky_box':
        r = random.random()
        if r < 0.3:
            bonus = random.randint(settings.get('lucky_box_money_min', 100), settings.get('lucky_box_money_max', 1000))
            user['money'] += bonus
            msg = f"🎁 +${bonus}!"
        elif r < 0.6:
            rand_item = random.choice(['booster', 'shield', 'analyst'])
            it = SHOP_ITEMS[rand_item]
            user['inventory'].append({
                'item_id': rand_item, 'name': it['name'], 'emoji': it['emoji'],
                'description': it['description'], 'category': it['category'], 'effect': it['effect']
            })
            msg = f"🎁 Выпал {it['emoji']} {it['name']}!"
        else:
            msg = "🎁 Ничего не выпало..."
    
    save_user(user_id, user)
    return True, msg, None

# ========== ПРОМОКОДЫ ==========
DEFAULT_PROMOCODES = {"WELCOME100": {"bonus": 100, "max_uses": 10, "used_count": 0}, "START500": {"bonus": 500, "max_uses": 10, "used_count": 0}}

def load_promos():
    if os.path.exists(PROMOCODES_FILE):
        with open(PROMOCODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_PROMOCODES.copy()

def save_promos(p):
    with open(PROMOCODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(p, f, indent=2, ensure_ascii=False)

def use_promo(user_id, code):
    code = code.upper()
    promos = load_promos()
    if code not in promos:
        return False, "❌ Промокод не найден"
    p = promos[code]
    if p['used_count'] >= p['max_uses']:
        return False, "❌ Промокод закончился"
    user = get_user(user_id)
    if code in user.get('used_promos', []):
        return False, "❌ Уже активирован"
    user['money'] += p['bonus']
    user['used_promos'] = user.get('used_promos', []) + [code]
    save_user(user_id, user)
    p['used_count'] += 1
    save_promos(promos)
    update_leaderboard()
    return True, f"✅ +${p['bonus']}"

def add_promo(code, bonus, max_uses):
    promos = load_promos()
    if code.upper() in promos:
        return False
    promos[code.upper()] = {'bonus': bonus, 'max_uses': max_uses, 'used_count': 0}
    save_promos(promos)
    return True

def del_promo(code):
    promos = load_promos()
    if code.upper() in promos:
        del promos[code.upper()]
        save_promos(promos)
        return True
    return False

# ========== СЕЗОН ==========
DEFAULT_SEASON = {'name': 'ВЕСНА', 'start': str(datetime.now()), 'end': str(datetime.now() + timedelta(days=14)), 'active': True}

def get_season():
    if os.path.exists(SEASON_FILE):
        with open(SEASON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_SEASON.copy()

def save_season(s):
    with open(SEASON_FILE, 'w', encoding='utf-8') as f:
        json.dump(s, f, indent=2, ensure_ascii=False)

def create_season(name, days):
    save_season({
        'name': name,
        'start': str(datetime.now()),
        'end': str(datetime.now() + timedelta(days=days)),
        'active': True
    })

def end_season():
    s = get_season()
    if not s['active']:
        return False, "❌ Уже завершён"
    s['active'] = False
    save_season(s)
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
    update_leaderboard()
    return True, "✅ Сезон завершён"

# ========== КЛАВИАТУРЫ ==========
def main_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="status"),
        types.InlineKeyboardButton("📈 Компании", callback_data="list"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🎟️ Промо", callback_data="promo"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    return kb

def back_kb(target):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data=target))
    return kb

def admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📝 Тексты", callback_data="admin_texts"),
        types.InlineKeyboardButton("🖼️ Фото", callback_data="admin_images"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("🎟️ Промокоды", callback_data="admin_promos"),
        types.InlineKeyboardButton("🏢 Компании", callback_data="admin_companies"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("🏆 Сезон", callback_data="admin_season"),
        types.InlineKeyboardButton("📦 Предметы", callback_data="admin_items"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return kb

def admin_texts_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📜 История", callback_data="edit_story"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="edit_help"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return kb

def admin_images_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key in IMAGES:
        name = {'main': '🏠 Главная', 'companies': '📈 Компании', 'stats': '📊 Статистика', 'inventory': '🎒 Инвентарь', 'shop': '🛒 Магазин', 'leaderboard': '🏆 Лидеры'}.get(key, key)
        kb.add(types.InlineKeyboardButton(name, callback_data=f"edit_img_{key}"))
    kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel"))
    return kb

def admin_settings_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💰 Стартовый капитал", callback_data="set_start_money"),
        types.InlineKeyboardButton("📈 Диапазон цен", callback_data="set_price_range"),
        types.InlineKeyboardButton("🎲 Случайный бонус", callback_data="set_random_bonus"),
        types.InlineKeyboardButton("🎁 Лаки бокс", callback_data="set_lucky_box"),
        types.InlineKeyboardButton("💎 Бонусы подписок", callback_data="set_sub_bonus"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return kb

def admin_users_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📋 Список", callback_data="user_list"),
        types.InlineKeyboardButton("🔍 Найти", callback_data="user_find"),
        types.InlineKeyboardButton("🚫 Забанить", callback_data="user_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="user_unban"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="user_give"),
        types.InlineKeyboardButton("📦 Выдать предмет", callback_data="user_item"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return kb

def shop_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📦 РАСХОДНИКИ", callback_data="cat_consumable"),
        types.InlineKeyboardButton("💎 ПОДПИСКИ", callback_data="cat_subscription"),
        types.InlineKeyboardButton("🎁 СПЕЦПРЕДЛОЖЕНИЯ", callback_data="cat_special"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return kb

def shop_category_kb(cat):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for iid, item in SHOP_ITEMS.items():
        if item['category'] == cat:
            kb.add(types.InlineKeyboardButton(f"{item['emoji']} {item['name']} — ${item['price']}", callback_data=f"buy_{iid}"))
    kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data="shop"))
    return kb

def inventory_kb(user):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(user.get('inventory', [])):
        kb.add(types.InlineKeyboardButton(f"{item['emoji']} {item['name']}", callback_data=f"use_{i}"))
    kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
    return kb

def companies_kb(page, total):
    kb = types.InlineKeyboardMarkup(row_width=3)
    if total > 1:
        row = []
        if page > 1:
            row.append(types.InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
        else:
            row.append(types.InlineKeyboardButton("◀️", callback_data="noop"))
        row.append(types.InlineKeyboardButton(f"{page}/{total}", callback_data="noop"))
        if page < total:
            row.append(types.InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
        else:
            row.append(types.InlineKeyboardButton("▶️", callback_data="noop"))
        kb.row(*row)
    kb.row(
        types.InlineKeyboardButton("🏠 Главная", callback_data="back_to_main"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
    )
    return kb

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "🚫 Вы забанены!")
        return
    
    name = m.from_user.username or m.from_user.first_name or f"User_{uid}"
    user = get_user(uid)
    user['username'] = name
    user['last_seen'] = str(datetime.now())
    save_user(uid, user)
    
    text = f"{STORY_TEXT}\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n\n📆 День: {user['day']}"
    bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_kb())

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "❌ Недостаточно прав!")
        return
    text = "🔧 *Админ-панель*\n\nВыберите действие:"
    bot.send_photo(m.chat.id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=admin_kb())

@bot.message_handler(commands=['help'])
def help_cmd(m):
    bot.send_message(m.chat.id, HELP_TEXT, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tbuy'])
def buy_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    try:
        _, ticker, amt = m.text.split()
        ticker = ticker.upper()
        amt = int(amt)
        companies = load_companies()
        if ticker not in companies:
            bot.reply_to(m, "❌ Нет такой компании")
            return
        user = get_user(m.from_user.id)
        price = companies[ticker]['price']
        total = price * amt
        if user['money'] >= total:
            user['money'] -= total
            user['portfolio'][ticker] = user['portfolio'].get(ticker, 0) + amt
            save_user(m.from_user.id, user)
            update_leaderboard()
            bot.reply_to(m, f"✅ Куплено {amt} {ticker} за ${total:,.2f}")
        else:
            bot.reply_to(m, f"❌ Нужно ${total:,.2f}")
    except:
        bot.reply_to(m, "❌ /tbuy AAPL 5")

@bot.message_handler(commands=['tsell'])
def sell_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    try:
        _, ticker, amt = m.text.split()
        ticker = ticker.upper()
        amt = int(amt)
        user = get_user(m.from_user.id)
        if ticker not in user['portfolio'] or user['portfolio'][ticker] < amt:
            bot.reply_to(m, f"❌ У вас {user['portfolio'].get(ticker, 0)} акций")
            return
        companies = load_companies()
        price = companies[ticker]['price']
        total = price * amt
        user['money'] += total
        user['portfolio'][ticker] -= amt
        if user['portfolio'][ticker] == 0:
            del user['portfolio'][ticker]
        save_user(m.from_user.id, user)
        update_leaderboard()
        bot.reply_to(m, f"✅ Продано {amt} {ticker} за ${total:,.2f}")
    except:
        bot.reply_to(m, "❌ /tsell AAPL 5")

@bot.message_handler(commands=['tnext'])
def next_cmd(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    update_prices()
    user = get_user(uid)
    user['day'] += 1
    save_user(uid, user)
    update_leaderboard()
    text = f"{STORY_TEXT}\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n\n📆 День: {user['day']}"
    bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_kb())

@bot.message_handler(commands=['tpromo'])
def promo_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    try:
        code = m.text.split()[1]
        ok, msg = use_promo(m.from_user.id, code)
        bot.reply_to(m, msg)
    except:
        bot.reply_to(m, "❌ /tpromo КОД")

@bot.message_handler(commands=['tlist'])
def list_cmd(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    user = get_user(uid)
    items, total = get_companies_page(1)
    pages = (total + 9) // 10
    text = f"📋 КОМПАНИИ (День {user['day']})\n\n"
    for t, d in items:
        change = get_price_change(d.get('prev_price', d['price']), d['price'])
        emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
        text += f"{t} — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change}\n\n"
    bot.send_photo(uid, IMAGES['companies'], caption=text, reply_markup=companies_kb(1, pages))

@bot.message_handler(commands=['tstats'])
def stats_cmd(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    user = get_user(uid)
    cap = calculate_capital(uid)
    text = f"📊 СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n💵 Капитал: ${cap:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n"
    if user.get('shields', 0) > 0:
        text += f"🛡️ Страховок: {user['shields']}\n"
    text += "\n📋 Портфель:\n"
    for t, a in user.get('portfolio', {}).items():
        companies = load_companies()
        if t in companies:
            text += f"{t}: {a} шт. (${a * companies[t]['price']:,.2f})\n"
    bot.send_photo(uid, IMAGES['stats'], caption=text, reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tleader'])
def leader_cmd(m):
    lb = get_leaderboard(10)
    text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
    for i, e in enumerate(lb, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
    bot.send_photo(m.chat.id, IMAGES['leaderboard'], caption=text, reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['inventory'])
def inventory_cmd(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    user = get_user(uid)
    text = "🎒 ИНВЕНТАРЬ\n\n"
    for i, item in enumerate(user.get('inventory', []), 1):
        text += f"{i}. {item['emoji']} {item['name']}\n"
    if not user.get('inventory'):
        text += "Пусто\n"
    text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
    bot.send_photo(uid, IMAGES['inventory'], caption=text, reply_markup=inventory_kb(user))

@bot.message_handler(commands=['shop'])
def shop_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    bot.send_photo(m.chat.id, IMAGES['shop'], caption="🛒 МАГАЗИН\n\nВыбери категорию:", reply_markup=shop_kb())

@bot.message_handler(commands=['promo'])
def promolist_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    promos = load_promos()
    text = "🎟️ ПРОМОКОДЫ\n\n"
    for code, d in promos.items():
        rem = d['max_uses'] - d['used_count']
        text += f"`{code}` — +${d['bonus']} (осталось {rem})\n"
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_companies_page(page=1, per_page=10):
    items = list(load_companies().items())
    total = len(items)
    start = (page - 1) * per_page
    return items[start:start+per_page], total

# ========== КОЛБЭКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    data = call.data
    
    if call.message.chat.type != 'private' and call.from_user.id != call.message.from_user.id:
        bot.answer_callback_query(call.id, "Это не твои кнопки 🤬", show_alert=True)
        return
    
    # Главное меню
    if data == "back_to_main":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        user = get_user(uid)
        text = f"{STORY_TEXT}\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n\n📆 День: {user['day']}"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"), call.message.chat.id, call.message.message_id, reply_markup=main_kb())
        bot.answer_callback_query(call.id)
        return
    
    # Админ-панель
    if data == "admin_panel":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        text = "🔧 *Админ-панель*\n\nВыберите действие:"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"), call.message.chat.id, call.message.message_id, reply_markup=admin_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_texts":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="📝 *Редактирование текстов*", parse_mode="Markdown", reply_markup=admin_texts_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "edit_story":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "📝 Отправьте новый текст истории (предыстории):")
        bot.register_next_step_handler(call.message, set_story)
        bot.answer_callback_query(call.id)
        return
    
    if data == "edit_help":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "❓ Отправьте новый текст помощи:")
        bot.register_next_step_handler(call.message, set_help)
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_images":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="🖼️ *Редактирование фото*", parse_mode="Markdown", reply_markup=admin_images_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("edit_img_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        key = data[9:]
        bot.send_message(uid, f"🖼️ Отправьте новое фото для раздела '{key}':")
        bot.register_next_step_handler(call.message, set_image, key)
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_settings":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="⚙️ *Настройки игры*", parse_mode="Markdown", reply_markup=admin_settings_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "set_start_money":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, f"💰 Текущий стартовый капитал: ${get_setting('start_money')}\n\nВведите новое значение:")
        bot.register_next_step_handler(call.message, set_start_money)
        bot.answer_callback_query(call.id)
        return
    
    if data == "set_price_range":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        minv = get_setting('price_change_min') * 100
        maxv = get_setting('price_change_max') * 100
        bot.send_message(uid, f"📈 Текущий диапазон: от {minv}% до {maxv}%\n\nВведите в формате: МИН МАКС\nПример: -10 10")
        bot.register_next_step_handler(call.message, set_price_range)
        bot.answer_callback_query(call.id)
        return
    
    if data == "set_random_bonus":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        minv = get_setting('random_bonus_min')
        maxv = get_setting('random_bonus_max')
        bot.send_message(uid, f"🎲 Текущий диапазон: от ${minv} до ${maxv}\n\nВведите в формате: МИН МАКС\nПример: 50 500")
        bot.register_next_step_handler(call.message, set_random_bonus)
        bot.answer_callback_query(call.id)
        return
    
    if data == "set_lucky_box":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        minv = get_setting('lucky_box_money_min')
        maxv = get_setting('lucky_box_money_max')
        bot.send_message(uid, f"🎁 Текущий диапазон: от ${minv} до ${maxv}\n\nВведите в формате: МИН МАКС\nПример: 100 1000")
        bot.register_next_step_handler(call.message, set_lucky_box)
        bot.answer_callback_query(call.id)
        return
    
    if data == "set_sub_bonus":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        vip = get_setting('vip_bonus')
        trader = get_setting('trader_bonus')
        inv = get_setting('investor_bonus')
        bot.send_message(uid, f"💎 Текущие бонусы:\nVIP: +{vip}%\nТрейдер: +{trader}%\nИнвестор: +{inv}%\n\nВведите в формате: VIP ТРЕЙДЕР ИНВЕСТОР\nПример: 10 15 20")
        bot.register_next_step_handler(call.message, set_sub_bonus)
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_users":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="👥 *Управление пользователями*", parse_mode="Markdown", reply_markup=admin_users_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_list":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        users = []
        for f in os.listdir(USERS_DIR):
            if f.endswith('.json'):
                uid_u = int(f[:-5])
                u = get_user(uid_u)
                if u:
                    users.append(f"{uid_u} - {u.get('username', 'Unknown')} - ${u['money']:,.2f}")
        text = "📋 *Список пользователей*\n\n" + "\n".join(users[:30])
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_find":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "🔍 Введите ID или username:")
        bot.register_next_step_handler(call.message, find_user)
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_ban":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "🚫 Введите ID пользователя для бана:")
        bot.register_next_step_handler(call.message, ban_user_cmd)
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_unban":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "✅ Введите ID пользователя для разбана:")
        bot.register_next_step_handler(call.message, unban_user_cmd)
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_give":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "💰 Введите ID и сумму через пробел:\nПример: 123456789 1000")
        bot.register_next_step_handler(call.message, give_money)
        bot.answer_callback_query(call.id)
        return
    
    if data == "user_item":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        bot.send_message(uid, "📦 Введите ID и ID предмета:\nДоступные: booster, shield, analyst, random, lucky_box\nПример: 123456789 booster")
        bot.register_next_step_handler(call.message, give_item)
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_promos":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        promos = load_promos()
        text = "🎟️ *ПРОМОКОДЫ*\n\n"
        for code, d in promos.items():
            text += f"`{code}` — +${d['bonus']} — {d['used_count']}/{d['max_uses']}\n"
        text += "\n/addpromo КОД БОНУС МАКС\n/delpromo КОД"
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_companies":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        comps = load_companies()
        text = "🏢 *КОМПАНИИ*\n\n"
        for t, d in list(comps.items())[:20]:
            text += f"{t} — {d['name']} — ${d['price']:,.2f}\n"
        text += "\n/editprice ТИКЕР ЦЕНА\n/addcompany ТИКЕР НАЗВАНИЕ ЦЕНА"
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_stats":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        total = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
        banned = len(load_banned())
        comps = len(load_companies())
        promos = len(load_promos())
        text = f"📊 *СТАТИСТИКА*\n\n👥 Игроков: {total}\n🚫 Забанено: {banned}\n🏢 Компаний: {comps}\n🎟️ Промокодов: {promos}"
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_season":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        s = get_season()
        text = f"🏆 *СЕЗОН*\n\nНазвание: {s['name']}\nАктивен: {'✅' if s['active'] else '❌'}\nНачало: {s['start'][:10]}\nКонец: {s['end'][:10]}\n\n/createseason НАЗВАНИЕ ДНЕЙ\n/endseason"
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    if data == "admin_items":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав")
            return
        text = "📦 *ПРЕДМЕТЫ*\n\n"
        for iid, item in SHOP_ITEMS.items():
            text += f"{item['emoji']} {item['name']} — ${item['price']}\n"
        text += "\n/edititemprice ID ЦЕНА"
        bot.send_message(uid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    # Остальные колбэки
    if data == "status":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        user = get_user(uid)
        cap = calculate_capital(uid)
        text = f"📊 СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n💵 Капитал: ${cap:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n"
        if user.get('shields', 0) > 0:
            text += f"🛡️ Страховок: {user['shields']}\n"
        text += "\n📋 Портфель:\n"
        for t, a in user.get('portfolio', {}).items():
            comps = load_companies()
            if t in comps:
                text += f"{t}: {a} шт. (${a * comps[t]['price']:,.2f})\n"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['stats'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=back_kb("back_to_main"))
        bot.answer_callback_query(call.id)
        return
    
    if data == "list":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        user = get_user(uid)
        items, total = get_companies_page(1)
        pages = (total + 9) // 10
        text = f"📋 КОМПАНИИ (День {user['day']})\n\n"
        for t, d in items:
            change = get_price_change(d.get('prev_price', d['price']), d['price'])
            emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
            text += f"{t} — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change}\n\n"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['companies'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=companies_kb(1, pages))
        bot.answer_callback_query(call.id)
        return
    
    if data == "next":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        update_prices()
        user = get_user(uid)
        user['day'] += 1
        save_user(uid, user)
        update_leaderboard()
        text = f"{STORY_TEXT}\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}\n\n📆 День: {user['day']}"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"), call.message.chat.id, call.message.message_id, reply_markup=main_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "leaderboard":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        lb = get_leaderboard(10)
        text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
        for i, e in enumerate(lb, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['leaderboard'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=back_kb("back_to_main"))
        bot.answer_callback_query(call.id)
        return
    
    if data == "shop":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['shop'], caption="🛒 МАГАЗИН\n\nВыбери категорию:"), call.message.chat.id, call.message.message_id, reply_markup=shop_kb())
        bot.answer_callback_query(call.id)
        return
    
    if data == "inventory":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        user = get_user(uid)
        text = "🎒 ИНВЕНТАРЬ\n\n"
        for i, item in enumerate(user.get('inventory', []), 1):
            text += f"{i}. {item['emoji']} {item['name']}\n"
        if not user.get('inventory'):
            text += "Пусто\n"
        text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['inventory'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=inventory_kb(user))
        bot.answer_callback_query(call.id)
        return
    
    if data == "promo":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        promos = load_promos()
        text = "🎟️ ПРОМОКОДЫ\n\n"
        for code, d in promos.items():
            rem = d['max_uses'] - d['used_count']
            text += f"`{code}` — +${d['bonus']} (осталось {rem})\n"
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))
        bot.answer_callback_query(call.id)
        return
    
    if data == "help":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=HELP_TEXT, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))
        bot.answer_callback_query(call.id)
        return
    
    # Категории магазина
    if data.startswith("cat_"):
        cat = data[4:]
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['shop'], caption=f"🛒 {cat.upper()}"), call.message.chat.id, call.message.message_id, reply_markup=shop_category_kb(cat))
        bot.answer_callback_query(call.id)
        return
    
    # Покупка предмета
    if data.startswith("buy_"):
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        item_id = data[4:]
        ok, msg = buy_item(uid, item_id)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            bot.edit_message_media(types.InputMediaPhoto(IMAGES['shop'], caption="🛒 МАГАЗИН\n\nВыбери категорию:"), call.message.chat.id, call.message.message_id, reply_markup=shop_kb())
        return
    
    # Использование предмета
    if data.startswith("use_"):
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        idx = int(data[4:])
        ok, msg, _ = use_item(uid, idx)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            user = get_user(uid)
            text = "🎒 ИНВЕНТАРЬ\n\n"
            for i, item in enumerate(user.get('inventory', []), 1):
                text += f"{i}. {item['emoji']} {item['name']}\n"
            if not user.get('inventory'):
                text += "Пусто\n"
            text += f"\n🏆 Кубков: {user.get('cubes', 0)}"
            bot.edit_message_media(types.InputMediaPhoto(IMAGES['inventory'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=inventory_kb(user))
        return
    
    # Пагинация компаний
    if data.startswith("page_"):
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        page = int(data[5:])
        user = get_user(uid)
        items, total = get_companies_page(page)
        pages = (total + 9) // 10
        text = f"📋 КОМПАНИИ (День {user['day']})\n\n"
        for t, d in items:
            change = get_price_change(d.get('prev_price', d['price']), d['price'])
            emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
            text += f"{t} — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change}\n\n"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['companies'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=companies_kb(page, pages))
        bot.answer_callback_query(call.id)
        return
    
    if data == "refresh":
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 Вы забанены!")
            return
        user = get_user(uid)
        items, total = get_companies_page(1)
        pages = (total + 9) // 10
        text = f"📋 КОМПАНИИ (День {user['day']})\n\n"
        for t, d in items:
            change = get_price_change(d.get('prev_price', d['price']), d['price'])
            emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
            text += f"{t} — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change}\n\n"
        bot.edit_message_media(types.InputMediaPhoto(IMAGES['companies'], caption=text), call.message.chat.id, call.message.message_id, reply_markup=companies_kb(1, pages))
        bot.answer_callback_query(call.id, "🔄 Обновлено")
        return
    
    if data == "noop":
        bot.answer_callback_query(call.id)
        return

# ========== ОБРАБОТЧИКИ ДЛЯ АДМИНА ==========
def set_story(message):
    if message.text:
        global STORY_TEXT
        STORY_TEXT = message.text
        bot.send_message(message.chat.id, "✅ История обновлена!")

def set_help(message):
    if message.text:
        global HELP_TEXT
        HELP_TEXT = message.text
        bot.send_message(message.chat.id, "✅ Помощь обновлена!")

def set_image(message, key):
    if message.photo:
        IMAGES[key] = message.photo[-1].file_id
        bot.send_message(message.chat.id, f"✅ Фото для '{key}' обновлено!")

def set_start_money(message):
    try:
        val = float(message.text)
        update_setting('start_money', val)
        bot.send_message(message.chat.id, f"✅ Стартовый капитал: ${val}")
    except:
        bot.send_message(message.chat.id, "❌ Введите число!")

def set_price_range(message):
    try:
        minv, maxv = map(float, message.text.split())
        update_setting('price_change_min', minv / 100)
        update_setting('price_change_max', maxv / 100)
        bot.send_message(message.chat.id, f"✅ Диапазон цен: от {minv}% до {maxv}%")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа!")

def set_random_bonus(message):
    try:
        minv, maxv = map(int, message.text.split())
        update_setting('random_bonus_min', minv)
        update_setting('random_bonus_max', maxv)
        bot.send_message(message.chat.id, f"✅ Случайный бонус: от ${minv} до ${maxv}")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа!")

def set_lucky_box(message):
    try:
        minv, maxv = map(int, message.text.split())
        update_setting('lucky_box_money_min', minv)
        update_setting('lucky_box_money_max', maxv)
        bot.send_message(message.chat.id, f"✅ Лаки бокс: от ${minv} до ${maxv}")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа!")

def set_sub_bonus(message):
    try:
        vip, trader, inv = map(int, message.text.split())
        update_setting('vip_bonus', vip)
        update_setting('trader_bonus', trader)
        update_setting('investor_bonus', inv)
        bot.send_message(message.chat.id, f"✅ Бонусы: VIP +{vip}%, Трейдер +{trader}%, Инвестор +{inv}%")
    except:
        bot.send_message(message.chat.id, "❌ Введите три числа!")

def find_user(message):
    search = message.text.lower()
    found = []
    for f in os.listdir(USERS_DIR):
        if f.endswith('.json'):
            uid_u = int(f[:-5])
            u = get_user(uid_u)
            if u:
                if search in str(uid_u) or (u.get('username') and search in u['username'].lower()):
                    found.append(f"ID: {uid_u}\nUsername: {u.get('username', 'Unknown')}\n💰 ${u['money']:,.2f}\n")
    if found:
        bot.send_message(message.chat.id, "\n".join(found[:10]))
    else:
        bot.send_message(message.chat.id, "❌ Не найдено")

def ban_user_cmd(message):
    try:
        uid_u = int(message.text)
        ban_user(uid_u)
        bot.send_message(message.chat.id, f"✅ Пользователь {uid_u} забанен!")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID!")

def unban_user_cmd(message):
    try:
        uid_u = int(message.text)
        unban_user(uid_u)
        bot.send_message(message.chat.id, f"✅ Пользователь {uid_u} разбанен!")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID!")

def give_money(message):
    try:
        parts = message.text.split()
        uid_u = int(parts[0])
        amt = float(parts[1])
        u = get_user(uid_u)
        if u:
            u['money'] += amt
            save_user(uid_u, u)
            update_leaderboard()
            bot.send_message(message.chat.id, f"✅ Выдано ${amt:,.2f} пользователю {uid_u}")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID и сумму!")

def give_item(message):
    try:
        parts = message.text.split()
        uid_u = int(parts[0])
        item_id = parts[1]
        if item_id not in SHOP_ITEMS:
            bot.send_message(message.chat.id, "❌ Предмет не найден")
            return
        u = get_user(uid_u)
        if u:
            item = SHOP_ITEMS[item_id]
            u['inventory'].append({
                'item_id': item_id,
                'name': item['name'],
                'emoji': item['emoji'],
                'description': item['description'],
                'category': item['category'],
                'effect': item['effect']
            })
            save_user(uid_u, u)
            bot.send_message(message.chat.id, f"✅ Выдан {item['emoji']} {item['name']} пользователю {uid_u}")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID и ID предмета!")

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['addpromo'])
def add_promo_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, code, bonus, mu = m.text.split()
        if add_promo(code, int(bonus), int(mu)):
            bot.reply_to(m, f"✅ Промокод {code} добавлен")
        else:
            bot.reply_to(m, "❌ Уже существует")
    except:
        bot.reply_to(m, "❌ /addpromo КОД БОНУС МАКС")

@bot.message_handler(commands=['delpromo'])
def del_promo_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        code = m.text.split()[1]
        if del_promo(code):
            bot.reply_to(m, f"✅ Промокод {code} удален")
        else:
            bot.reply_to(m, "❌ Не найден")
    except:
        bot.reply_to(m, "❌ /delpromo КОД")

@bot.message_handler(commands=['editprice'])
def edit_price_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, ticker, price = m.text.split()
        ticker = ticker.upper()
        price = float(price)
        comps = load_companies()
        if ticker in comps:
            comps[ticker]['price'] = price
            comps[ticker]['prev_price'] = price
            save_companies(comps)
            bot.reply_to(m, f"✅ {ticker} цена: ${price}")
        else:
            bot.reply_to(m, "❌ Компания не найдена")
    except:
        bot.reply_to(m, "❌ /editprice AAPL 175.50")

@bot.message_handler(commands=['addcompany'])
def add_company_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        ticker = parts[1].upper()
        name = parts[2]
        price = float(parts[3])
        comps = load_companies()
        comps[ticker] = {'name': name, 'price': price, 'prev_price': price}
        save_companies(comps)
        bot.reply_to(m, f"✅ Компания {ticker} добавлена")
    except:
        bot.reply_to(m, "❌ /addcompany AAPL Apple 175.50")

@bot.message_handler(commands=['edititemprice'])
def edit_item_price_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, item_id, price = m.text.split()
        price = float(price)
        if item_id in SHOP_ITEMS:
            SHOP_ITEMS[item_id]['price'] = price
            bot.reply_to(m, f"✅ {SHOP_ITEMS[item_id]['name']} цена: ${price}")
        else:
            bot.reply_to(m, "❌ Предмет не найден")
    except:
        bot.reply_to(m, "❌ /edititemprice booster 500")

@bot.message_handler(commands=['createseason'])
def create_season_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, name, days = m.text.split()
        create_season(name, int(days))
        bot.reply_to(m, f"✅ Сезон '{name}' на {days} дней")
    except:
        bot.reply_to(m, "❌ /createseason ВЕСНА 14")

@bot.message_handler(commands=['endseason'])
def end_season_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    ok, msg = end_season()
    bot.reply_to(m, msg)

@bot.message_handler(commands=['addleader'])
def add_leader_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    update_leaderboard()
    bot.reply_to(m, "✅ Таблица лидеров обновлена")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен!")
    print("✅ Админ-панель: /admin")
    print(f"✅ Админ ID: {ADMIN_ID}")
    print("✅ Бот готов к работе!")
    bot.infinity_polling()