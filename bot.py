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
SETTINGS_FILE = "settings.json"  # Новый файл для настроек
BANNED_USERS_FILE = "banned_users.json"  # Файл для забаненных пользователей

if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== НАСТРОЙКИ ПО УМОЛЧАНИЮ ==========
DEFAULT_SETTINGS = {
    'story_text': "📜 *Небольшая предыстория...*\n\nТы обычный человек, который однажды утром открыл Telegram и наткнулся на странного бота.\nВ описании было сказано: _«Хочешь стать миллионером? Начни прямо сейчас и покори биржу!»_.\n\nСначала ты подумал, что это очередной развод, но любопытство взяло верх.\nТы запустил бота и... оказался в мире, где каждое твоё решение может принести состояние или оставить с пустым кошельком.\n\nТеперь ты трейдер. И от твоих решений зависит, войдёшь ли ты в историю как легенда или исчезнешь в бездне убытков.\n\nДобро пожаловать в *Terminal Trade*.",
    'help_text': "📚 *Помощь по игре*\n\n*Команды:*\n/start - начать игру\n/help - эта помощь\n/tbuy КОМПАНИЯ КОЛ-ВО - купить акции\n/tsell КОМПАНИЯ КОЛ-ВО - продать акции\n/tnext - следующий день\n/tstats - твоя статистика\n/tlist - список компаний\n/tleader - таблица лидеров\n/tpromo КОД - активировать промокод\n/promo - список промокодов\n/shop - магазин\n/inventory - инвентарь\n\n*Предметы:*\n🚀 Ускоритель - цены растут быстрее 24ч\n🛡️ Страховка - защита от 1 убытка\n📊 Аналитик - прогноз цен\n🎲 Рандом - случайный бонус\n💎 VIP - +10% к доходу 30 дней\n📈 Трейдер PRO - +15% к доходу 30 дней\n💰 Инвестор - +20% к доходу 30 дней\n🎁 Лаки бокс - случайный приз",
    'start_money': 1000.0,
    'price_change_min': -0.1,
    'price_change_max': 0.1,
    'booster_multiplier': 1.5,
    'vip_bonus': 10,
    'trader_bonus': 15,
    'investor_bonus': 20,
    'random_bonus_min': 50,
    'random_bonus_max': 500,
    'lucky_box_money_min': 100,
    'lucky_box_money_max': 1000,
    'shop_items': SHOP_ITEMS  # Сохраняем товары в настройки
}

# ========== КАРТИНКИ ==========
IMAGES = {
    'main': 'https://s10.iimage.su/s/05/gIKluIYxLgUpL28XWRh1IzTmdY4DzqMQuX8v39ee9.jpg',
    'companies': 'https://s10.iimage.su/s/05/gf3a1gxxMZn6ArfLKZD3JlzVhy83Bm1cGvNVjC0vI.jpg',
    'stats': 'https://s10.iimage.su/s/05/gioJHlUxz7G3Udtvbpc4t3CAoCSsryhLnSFXWdayc.jpg',
    'inventory': 'https://s10.iimage.su/s/05/grMXdR3xwFaLXdQ74TR9rz7zu8Wb60ezeX89JKuzm.jpg',
    'shop': 'https://s10.iimage.su/s/05/gbuaUsrxIjSjwQcGwcZrUaNcbFXzpITC2qFzhFzrd.jpg',
    'leaderboard': 'https://s10.iimage.su/s/05/gYoBW3cxowvFLbKdb8GJCDKWoEAcQD5DJa0zHCQt6.jpg'
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

# ========== НАСТРОЙКИ ==========
def load_settings():
    settings = load_json(SETTINGS_FILE)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        save_json(SETTINGS_FILE, settings)
    return settings

def save_settings(settings):
    save_json(SETTINGS_FILE, settings)

def get_setting(key):
    return load_settings().get(key, DEFAULT_SETTINGS.get(key))

def update_setting(key, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)

# ========== БАН ==========
def load_banned_users():
    return load_json(BANNED_USERS_FILE)

def save_banned_users(banned):
    save_json(BANNED_USERS_FILE, banned)

def is_banned(user_id):
    banned = load_banned_users()
    return user_id in banned

def ban_user(user_id):
    banned = load_banned_users()
    banned[user_id] = str(datetime.now())
    save_banned_users(banned)

def unban_user(user_id):
    banned = load_banned_users()
    if user_id in banned:
        del banned[user_id]
        save_banned_users(banned)

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
    settings = load_settings()
    change_min = settings.get('price_change_min', -0.1)
    change_max = settings.get('price_change_max', 0.1)
    booster_active = False  # Здесь можно проверить глобальный бустер
    
    for ticker, data in companies.items():
        old = data['price']
        change = random.uniform(change_min, change_max)
        if booster_active:
            change = change * settings.get('booster_multiplier', 1.5)
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
    if is_banned(user_id):
        return None
    
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
    with open(get_user_file(user_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_user_last_seen(user_id):
    user = get_user(user_id)
    if user:
        user['last_seen'] = str(datetime.now())
        save_user(user_id, user)

def get_portfolio(user_id):
    user = get_user(user_id)
    if not user:
        return []
    companies = load_companies()
    return [{'ticker': t, 'amount': a, 'price': companies[t]['price'], 'name': companies[t]['name']}
            for t, a in user.get('portfolio', {}).items() if t in companies]

def calculate_capital(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    companies = load_companies()
    total = user['money']
    for t, a in user.get('portfolio', {}).items():
        if t in companies:
            total += a * companies[t]['price']
    return round(total, 2)

def buy_stock(user_id, ticker, amount):
    if is_banned(user_id):
        return False, "❌ Вы забанены"
    
    companies = load_companies()
    if ticker not in companies:
        return False, "❌ Нет такой компании"
    user = get_user(user_id)
    if not user:
        return False, "❌ Пользователь не найден"
    
    price = companies[ticker]['price']
    total = price * amount
    if user['money'] >= total:
        user['money'] -= total
        user['money'] = round(user['money'], 2)
        user['portfolio'][ticker] = user['portfolio'].get(ticker, 0) + amount
        save_user(user_id, user)
        update_leaderboard()
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    return False, f"❌ Нужно ${total:,.2f}"

def sell_stock(user_id, ticker, amount):
    if is_banned(user_id):
        return False, "❌ Вы забанены"
    
    companies = load_companies()
    user = get_user(user_id)
    if not user:
        return False, "❌ Пользователь не найден"
    
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
    update_leaderboard()
    return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"

def buy_item(user_id, item_id):
    if is_banned(user_id):
        return False, "❌ Вы забанены"
    
    user = get_user(user_id)
    if not user:
        return False, "❌ Пользователь не найден"
    
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
    update_leaderboard()
    return True, f"✅ Куплен {item['emoji']} {item['name']}"

def activate_item(user_id, idx):
    if is_banned(user_id):
        return False, "❌ Вы забанены", None
    
    user = get_user(user_id)
    if not user:
        return False, "❌ Пользователь не найден", None
    
    if idx < 0 or idx >= len(user['inventory']):
        return False, "❌ Предмет не найден", None
    
    item = user['inventory'].pop(idx)
    effect_message = ""
    effect_data = None
    settings = load_settings()
    
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
        bonus = random.randint(settings.get('random_bonus_min', 50), settings.get('random_bonus_max', 500))
        user['money'] += bonus
        effect_message = f"🎲 Случайный бонус: +${bonus}!"
        effect_data = {'type': 'random', 'bonus': bonus}
        
    elif item['effect'] in ['vip', 'trader', 'investor']:
        duration = 30
        if item['effect'] == 'vip':
            bonus = settings.get('vip_bonus', 10)
        elif item['effect'] == 'trader':
            bonus = settings.get('trader_bonus', 15)
        else:
            bonus = settings.get('investor_bonus', 20)
            
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
            bonus = random.randint(settings.get('lucky_box_money_min', 100), settings.get('lucky_box_money_max', 1000))
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
            if is_banned(uid):
                continue
            user = get_user(uid)
            if user:
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
    if is_banned(user_id):
        return False, "❌ Вы забанены"
    
    p = load_promocodes()
    code = code.upper()
    if code not in p:
        return False, "❌ Промокод не найден"
    promo = p[code]
    if promo['used_count'] >= promo['max_uses']:
        return False, "❌ Промокод закончился"
    user = get_user(user_id)
    if not user:
        return False, "❌ Пользователь не найден"
    if code in user.get('used_promos', []):
        return False, "❌ Уже активирован"
    user['money'] += promo['bonus']
    user['used_promos'] = user.get('used_promos', []) + [code]
    save_user(user_id, user)
    promo['used_count'] += 1
    save_promocodes(p)
    update_leaderboard()
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
        if u:
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

def admin_panel_kb():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Изменить текст", callback_data="admin_text"),
        types.InlineKeyboardButton("🖼️ Изменить фото", callback_data="admin_images"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("🎟️ Промокоды", callback_data="admin_promos"),
        types.InlineKeyboardButton("🏢 Компании", callback_data="admin_companies"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("🏆 Сезон", callback_data="admin_season"),
        types.InlineKeyboardButton("📦 Предметы", callback_data="admin_items"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup

def admin_text_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📜 История", callback_data="edit_story"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="edit_help"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return markup

def admin_images_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key in IMAGES.keys():
        name = {
            'main': '🏠 Главная',
            'companies': '📈 Компании',
            'stats': '📊 Статистика',
            'inventory': '🎒 Инвентарь',
            'shop': '🛒 Магазин',
            'leaderboard': '🏆 Лидеры'
        }.get(key, key)
        markup.add(types.InlineKeyboardButton(name, callback_data=f"edit_image_{key}"))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel"))
    return markup

def admin_settings_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 Стартовый капитал", callback_data="edit_start_money"),
        types.InlineKeyboardButton("📈 Диапазон изменения цен", callback_data="edit_price_range"),
        types.InlineKeyboardButton("🎲 Случайный бонус", callback_data="edit_random_bonus"),
        types.InlineKeyboardButton("🎁 Лаки бокс", callback_data="edit_lucky_box"),
        types.InlineKeyboardButton("💎 Бонусы подписок", callback_data="edit_subscription_bonus"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return markup

def admin_users_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📋 Список пользователей", callback_data="admin_user_list"),
        types.InlineKeyboardButton("🔍 Найти пользователя", callback_data="admin_user_find"),
        types.InlineKeyboardButton("🚫 Забанить пользователя", callback_data="admin_user_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="admin_user_unban"),
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_user_give"),
        types.InlineKeyboardButton("📦 Выдать предмет", callback_data="admin_user_item"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
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
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
    
    text = "🔧 *Админ-панель*\n\nВыберите действие:"
    if IMAGES.get('main'):
        bot.send_photo(message.chat.id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=admin_panel_kb())
    else:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_panel_kb())
        
@bot.message_handler(commands=['start', 'trade'])
def start_cmd(message):
    uid = message.from_user.id
    
    if is_banned(uid):
        bot.send_message(uid, "🚫 Вы забанены в игре!")
        return
    
    name = message.from_user.username or message.from_user.first_name or f"User_{uid}"
    user = get_user(uid)
    if not user:
        bot.send_message(uid, "🚫 Вы забанены в игре!")
        return
    
    user['username'] = name
    user['last_seen'] = str(datetime.now())
    save_user(uid, user)
    
    season = get_current_season()
    d, h = get_season_time_left()
    time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
    
    story = get_setting('story_text')
    text = f"{story}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
    
    if IMAGES.get('main'):
        bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = "🔧 *Админ-панель*\n\nВыберите действие:"
    if IMAGES.get('main'):
        bot.send_photo(message.chat.id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=admin_panel_kb())
    else:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_panel_kb())

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = get_setting('help_text')
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tbuy'])
def buy_stock_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
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
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
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
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    update_company_prices()
    user = get_user(uid)
    if not user:
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    user['day'] += 1
    user['last_seen'] = str(datetime.now())
    save_user(uid, user)
    update_leaderboard()
    
    season = get_current_season()
    d, h = get_season_time_left()
    time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
    
    story = get_setting('story_text')
    text = f"{story}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
    
    if IMAGES.get('main'):
        bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=['tpromo'])
def promo_activate_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
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
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    user = get_user(uid)
    if not user:
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
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
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    user = get_user(uid)
    if not user:
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
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
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
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
    if is_banned(uid):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    user = get_user(uid)
    if not user:
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
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
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
    text = "🛒 МАГАЗИН\n\nВыбери категорию:"
    if IMAGES.get('shop'):
        bot.send_photo(m.chat.id, IMAGES['shop'], caption=text, reply_markup=shop_kb())
    else:
        bot.send_message(m.chat.id, text, reply_markup=shop_kb())

@bot.message_handler(commands=['promo'])
def promo_list_cmd(m):
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Вы забанены!")
        return
    
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
    
    # Защита от чужих кнопок
    if call.message.chat.type != 'private' and call.from_user.id != call.message.from_user.id:
        bot.answer_callback_query(call.id, "Это не твои кнопки 🤬", show_alert=True)
        return
    
    try:
        # ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ =====
        if data == "back_to_main":
            user = get_user(uid)
            if is_banned(uid) or not user:
                bot.answer_callback_query(call.id, "🚫 Вы забанены!")
                return
                
            season = get_current_season()
            d, h = get_season_time_left()
            time_left = f"\n📅 До конца сезона: {d}д {h}ч" if d else ""
            
            story = get_setting('story_text')
            text = f"{story}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
            
            if IMAGES.get('main'):
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

        # ===== АДМИН-ПАНЕЛЬ =====
        if data == "admin_panel":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "🔧 *Админ-панель*\n\nВыберите действие:"
            if IMAGES.get('main'):
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=admin_panel_kb()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=admin_panel_kb()
                )
            bot.answer_callback_query(call.id)
            return

        # ===== ИЗМЕНЕНИЕ ТЕКСТА =====
        if data == "admin_text":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "📝 *Редактирование текстов*\n\nВыберите текст для редактирования:"
            bot.edit_message_caption(
                call.message.chat.id,
                call.message.message_id,
                caption=text,
                parse_mode="Markdown",
                reply_markup=admin_text_kb()
            )
            bot.answer_callback_query(call.id)
            return

        if data == "edit_story":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "📝 Отправьте новый текст для истории (предыстории).\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_story_text)
            bot.answer_callback_query(call.id)
            return

        if data == "edit_help":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "❓ Отправьте новый текст для раздела помощи.\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_help_text)
            bot.answer_callback_query(call.id)
            return

        # ===== ИЗМЕНЕНИЕ ФОТО =====
        if data == "admin_images":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "🖼️ *Редактирование фото*\n\nВыберите раздел для изменения фото:"
            bot.edit_message_caption(
                call.message.chat.id,
                call.message.message_id,
                caption=text,
                parse_mode="Markdown",
                reply_markup=admin_images_kb()
            )
            bot.answer_callback_query(call.id)
            return

        if data.startswith("edit_image_"):
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            image_key = data[11:]
            bot.send_message(uid, f"🖼️ Отправьте новое фото для раздела '{image_key}'\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_image, image_key)
            bot.answer_callback_query(call.id)
            return

        # ===== НАСТРОЙКИ =====
        if data == "admin_settings":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "⚙️ *Настройки игры*\n\nВыберите параметр для изменения:"
            bot.edit_message_caption(
                call.message.chat.id,
                call.message.message_id,
                caption=text,
                parse_mode="Markdown",
                reply_markup=admin_settings_kb()
            )
            bot.answer_callback_query(call.id)
            return

        if data == "edit_start_money":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            current = get_setting('start_money')
            bot.send_message(uid, f"💰 Текущий стартовый капитал: ${current}\n\nВведите новое значение (число):\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_start_money)
            bot.answer_callback_query(call.id)
            return

        if data == "edit_price_range":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            current_min = get_setting('price_change_min')
            current_max = get_setting('price_change_max')
            bot.send_message(uid, f"📈 Текущий диапазон изменения цен: от {current_min*100}% до {current_max*100}%\n\nВведите новый диапазон в формате: МИН МАКС\nПример: -0.1 0.1\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_price_range)
            bot.answer_callback_query(call.id)
            return

        if data == "edit_random_bonus":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            current_min = get_setting('random_bonus_min')
            current_max = get_setting('random_bonus_max')
            bot.send_message(uid, f"🎲 Текущий диапазон случайного бонуса: от ${current_min} до ${current_max}\n\nВведите новый диапазон в формате: МИН МАКС\nПример: 50 500\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_random_bonus)
            bot.answer_callback_query(call.id)
            return

        if data == "edit_lucky_box":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            current_min = get_setting('lucky_box_money_min')
            current_max = get_setting('lucky_box_money_max')
            bot.send_message(uid, f"🎁 Текущий диапазон денежного приза в лаки боксе: от ${current_min} до ${current_max}\n\nВведите новый диапазон в формате: МИН МАКС\nПример: 100 1000\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_lucky_box)
            bot.answer_callback_query(call.id)
            return

        if data == "edit_subscription_bonus":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            vip = get_setting('vip_bonus')
            trader = get_setting('trader_bonus')
            investor = get_setting('investor_bonus')
            bot.send_message(uid, f"💎 Текущие бонусы подписок:\nVIP: +{vip}%\nТрейдер PRO: +{trader}%\nИнвестор: +{investor}%\n\nВведите новые значения в формате: VIP ТРЕЙДЕР ИНВЕСТОР\nПример: 10 15 20\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, set_subscription_bonus)
            bot.answer_callback_query(call.id)
            return

        # ===== ПОЛЬЗОВАТЕЛИ =====
        if data == "admin_users":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "👥 *Управление пользователями*\n\nВыберите действие:"
            bot.edit_message_caption(
                call.message.chat.id,
                call.message.message_id,
                caption=text,
                parse_mode="Markdown",
                reply_markup=admin_users_kb()
            )
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_list":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            users = []
            for f in os.listdir(USERS_DIR):
                if f.endswith('.json'):
                    uid_user = int(f[:-5])
                    user = get_user(uid_user)
                    if user:
                        users.append(f"{uid_user} - {user.get('username', 'Unknown')} - ${user['money']:,.2f}")
            
            text = "📋 *Список пользователей*\n\n" + "\n".join(users[:50])
            if len(users) > 50:
                text += f"\n... и еще {len(users)-50}"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_ban":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "🚫 Введите ID пользователя для бана:\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, ban_user_cmd)
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_unban":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "✅ Введите ID пользователя для разбана:\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, unban_user_cmd)
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_give":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "💰 Введите ID пользователя и сумму через пробел:\nПример: 123456789 1000\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, give_money_cmd)
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_item":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "📦 Введите ID пользователя и ID предмета через пробел:\nДоступные предметы: booster, shield, analyst, random, lucky_box\nПример: 123456789 booster\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, give_item_cmd)
            bot.answer_callback_query(call.id)
            return

        if data == "admin_user_find":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            bot.send_message(uid, "🔍 Введите ID или username пользователя для поиска:\nОтправьте 'отмена' для отмены.")
            bot.register_next_step_handler(call.message, find_user_cmd)
            bot.answer_callback_query(call.id)
            return

        # ===== ПРОМОКОДЫ =====
        if data == "admin_promos":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            promos = load_promocodes()
            text = "🎟️ *Управление промокодами*\n\n"
            for code, d in promos.items():
                text += f"`{code}` — +${d['bonus']} — {d['used_count']}/{d['max_uses']}\n"
            text += "\n/addpromo КОД БОНУС МАКС - создать\n/delpromo КОД - удалить"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        # ===== КОМПАНИИ =====
        if data == "admin_companies":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            companies = load_companies()
            text = "🏢 *Управление компаниями*\n\n"
            for t, d in list(companies.items())[:20]:
                text += f"{t} — {d['name']} — ${d['price']:,.2f}\n"
            text += "\n/editprice ТИКЕР ЦЕНА - изменить цену\n/addcompany ТИКЕР НАЗВАНИЕ ЦЕНА - добавить"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        # ===== СТАТИСТИКА =====
        if data == "admin_stats":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            total_users = len([f for f in os.listdir(USERS_DIR) if f.endswith('.json')])
            banned_users = len(load_banned_users())
            active_users = total_users - banned_users
            
            total_money = 0
            for f in os.listdir(USERS_DIR):
                if f.endswith('.json'):
                    user = get_user(int(f[:-5]))
                    if user:
                        total_money += user['money']
            
            promos = load_promocodes()
            total_promos = len(promos)
            total_acts = sum(p['used_count'] for p in promos.values())
            companies = load_companies()
            
            text = f"📊 *СТАТИСТИКА ИГРЫ*\n\n👥 Всего игроков: {total_users}\n🚫 Забанено: {banned_users}\n✅ Активных: {active_users}\n💰 Всего денег: ${total_money:,.2f}\n🎟️ Промокодов: {total_promos}\n🎫 Активаций: {total_acts}\n🏢 Компаний: {len(companies)}"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        # ===== СЕЗОН =====
        if data == "admin_season":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            season = get_current_season()
            d, h = get_season_time_left()
            text = f"🏆 *Управление сезоном*\n\nНазвание: {season['name']}\nАктивен: {'✅' if season['active'] else '❌'}\nНачало: {season['start'][:10]}\nКонец: {season['end'][:10]}\nОсталось: {d}д {h}ч" if d else "Завершен"
            text += "\n\n/createseason НАЗВАНИЕ ДНЕЙ - создать сезон\n/endseason - завершить сезон"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        # ===== ПРЕДМЕТЫ =====
        if data == "admin_items":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Недостаточно прав")
                return
            text = "📦 *Управление предметами*\n\n"
            for item_id, item in SHOP_ITEMS.items():
                text += f"{item['emoji']} {item['name']} — ${item['price']} ({item['category']})\n"
            text += "\n/edititemprice ID ЦЕНА - изменить цену\n/additem ID НАЗВАНИЕ ЦЕНА - добавить предмет"
            bot.send_message(uid, text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return

        # ===== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (без изменений) =====
        # ... (здесь остаются все остальные обработчики из исходного кода)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")

# ========== ОБРАБОТЧИКИ ДЛЯ АДМИНА ==========
def set_story_text(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    update_setting('story_text', message.text)
    bot.send_message(message.chat.id, f"✅ История обновлена!")

def set_help_text(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    update_setting('help_text', message.text)
    bot.send_message(message.chat.id, f"✅ Помощь обновлена!")

def set_image(message, image_key):
    if message.text and message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    
    if message.photo:
        file_id = message.photo[-1].file_id
        IMAGES[image_key] = file_id
        bot.send_message(message.chat.id, f"✅ Фото для '{image_key}' обновлено!")
    else:
        bot.send_message(message.chat.id, "❌ Отправьте фото!")

def set_start_money(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        value = float(message.text)
        update_setting('start_money', value)
        bot.send_message(message.chat.id, f"✅ Стартовый капитал установлен: ${value}")
    except:
        bot.send_message(message.chat.id, "❌ Введите число!")

def set_price_range(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        min_val, max_val = map(float, message.text.split())
        update_setting('price_change_min', min_val)
        update_setting('price_change_max', max_val)
        bot.send_message(message.chat.id, f"✅ Диапазон изменения цен: от {min_val*100}% до {max_val*100}%")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа через пробел!")

def set_random_bonus(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        min_val, max_val = map(int, message.text.split())
        update_setting('random_bonus_min', min_val)
        update_setting('random_bonus_max', max_val)
        bot.send_message(message.chat.id, f"✅ Случайный бонус: от ${min_val} до ${max_val}")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа через пробел!")

def set_lucky_box(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        min_val, max_val = map(int, message.text.split())
        update_setting('lucky_box_money_min', min_val)
        update_setting('lucky_box_money_max', max_val)
        bot.send_message(message.chat.id, f"✅ Лаки бокс: от ${min_val} до ${max_val}")
    except:
        bot.send_message(message.chat.id, "❌ Введите два числа через пробел!")

def set_subscription_bonus(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        vip, trader, investor = map(int, message.text.split())
        update_setting('vip_bonus', vip)
        update_setting('trader_bonus', trader)
        update_setting('investor_bonus', investor)
        bot.send_message(message.chat.id, f"✅ Бонусы подписок:\nVIP: +{vip}%\nТрейдер PRO: +{trader}%\nИнвестор: +{investor}%")
    except:
        bot.send_message(message.chat.id, "❌ Введите три числа через пробел!")

def ban_user_cmd(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.send_message(message.chat.id, f"✅ Пользователь {uid} забанен!")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID!")

def unban_user_cmd(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.send_message(message.chat.id, f"✅ Пользователь {uid} разбанен!")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID!")

def give_money_cmd(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        parts = message.text.split()
        uid = int(parts[0])
        amount = float(parts[1])
        user = get_user(uid)
        if user:
            user['money'] += amount
            save_user(uid, user)
            update_leaderboard()
            bot.send_message(message.chat.id, f"✅ Выдано ${amount:,.2f} пользователю {uid}")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID и сумму!")

def give_item_cmd(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    try:
        parts = message.text.split()
        uid = int(parts[0])
        item_id = parts[1]
        
        if item_id not in SHOP_ITEMS:
            bot.send_message(message.chat.id, "❌ Предмет не найден!")
            return
        
        user = get_user(uid)
        if user:
            item = SHOP_ITEMS[item_id]
            user['inventory'].append({
                'item_id': item_id,
                'name': item['name'],
                'emoji': item['emoji'],
                'description': item['description'],
                'category': item['category'],
                'effect': item.get('effect', 'none')
            })
            save_user(uid, user)
            bot.send_message(message.chat.id, f"✅ Выдан предмет {item['emoji']} {item['name']} пользователю {uid}")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Введите ID и ID предмета!")

def find_user_cmd(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "❌ Отменено")
        return
    
    search = message.text.lower()
    found = []
    
    for f in os.listdir(USERS_DIR):
        if f.endswith('.json'):
            uid = int(f[:-5])
            user = get_user(uid)
            if user:
                username = user.get('username', '').lower()
                if search in str(uid) or search in username:
                    cap = calculate_capital(uid)
                    found.append(f"ID: {uid}\nUsername: {user.get('username', 'Unknown')}\n💰 Баланс: ${user['money']:,.2f}\n💵 Капитал: ${cap:,.2f}\n🏆 Кубков: {user.get('cubes',0)}\n")
    
    if found:
        bot.send_message(message.chat.id, "\n".join(found[:10]))
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['addpromo'])
def admin_add_promo(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, code, bonus, mu = m.text.split()
        if add_promocode(code, int(bonus), int(mu)):
            bot.reply_to(m, f"✅ Промокод {code} добавлен")
        else:
            bot.reply_to(m, "❌ Уже существует")
    except:
        bot.reply_to(m, "❌ /addpromo КОД БОНУС МАКС")

@bot.message_handler(commands=['delpromo'])
def admin_del_promo(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        code = m.text.split()[1].upper()
        if delete_promocode(code):
            bot.reply_to(m, f"✅ Промокод {code} удалён")
        else:
            bot.reply_to(m, "❌ Не найден")
    except:
        bot.reply_to(m, "❌ /delpromo КОД")

@bot.message_handler(commands=['editprice'])
def admin_edit_price(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, ticker, price = m.text.split()
        ticker = ticker.upper()
        price = float(price)
        companies = load_companies()
        if ticker in companies:
            companies[ticker]['price'] = price
            companies[ticker]['prev_price'] = price
            save_companies(companies)
            bot.reply_to(m, f"✅ {ticker} цена установлена: ${price}")
        else:
            bot.reply_to(m, "❌ Компания не найдена")
    except:
        bot.reply_to(m, "❌ /editprice AAPL 175.50")

@bot.message_handler(commands=['addcompany'])
def admin_add_company(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        ticker = parts[1].upper()
        name = parts[2]
        price = float(parts[3])
        companies = load_companies()
        companies[ticker] = {'name': name, 'price': price, 'prev_price': price}
        save_companies(companies)
        bot.reply_to(m, f"✅ Компания {ticker} добавлена")
    except:
        bot.reply_to(m, "❌ /addcompany TICKER NAME PRICE")

@bot.message_handler(commands=['edititemprice'])
def admin_edit_item_price(m):
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
        bot.reply_to(m, "❌ /edititemprice item_id 500")

@bot.message_handler(commands=['createseason'])
def admin_create_season(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, name, days = m.text.split()
        create_season(name, int(days))
        bot.reply_to(m, f"✅ Сезон '{name}' на {days} дней")
    except:
        bot.reply_to(m, "❌ /createseason НАЗВАНИЕ ДНЕЙ")

@bot.message_handler(commands=['endseason'])
def admin_end_season(m):
    if m.from_user.id != ADMIN_ID:
        return
    ok, msg = end_season()
    bot.reply_to(m, msg)

@bot.message_handler(commands=['adminhelp'])
def admin_help(m):
    if m.from_user.id != ADMIN_ID:
        return
    text = """
🔧 *АДМИН-КОМАНДЫ*

*Основные:*
/admin - открыть админ-панель
/addleader - обновить таблицу лидеров

*Промокоды:*
/addpromo КОД БОНУС МАКС - создать
/delpromo КОД - удалить

*Компании:*
/editprice ТИКЕР ЦЕНА - изменить цену
/addcompany ТИКЕР НАЗВАНИЕ ЦЕНА - добавить

*Предметы:*
/edititemprice ID ЦЕНА - изменить цену

*Сезоны:*
/createseason НАЗВАНИЕ ДНЕЙ - создать
/endseason - завершить

*Старые команды:*
/admingive ID СУММА
/admintake ID СУММА
/adminreset ID
/adminstats
/admintop
"""
    bot.reply_to(m, text, parse_mode="Markdown")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен")
    print("✅ Админ-панель добавлена")
    print("✅ Настройки сохранены в settings.json")
    print("✅ Система банов добавлена")
    print("✅ Бот работает в чатах и ЛС")
    bot.infinity_polling()