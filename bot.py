import telebot
from telebot import types
import json
import os
import random
from datetime import datetime, timedelta

# ========== ТВОИ ДАННЫЕ ==========
TOKEN = "8795547713:AAF9AxpaZDhsZS6XTIDn6QveKOvC1F5E2YY"
YOUR_ID = 7040677455  # Только ты!

bot = telebot.TeleBot(TOKEN)

# ========== ПАПКИ ==========
os.makedirs('users', exist_ok=True)

# ========== JSON ФУНКЦИИ ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== ПОЛЬЗОВАТЕЛИ ==========
def get_user(user_id):
    path = f'users/{user_id}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        user = {
            'id': user_id,
            'name': None,
            'username': None,
            'money': 10000.0,
            'day': 1,
            'cubes': 0,
            'shields': 0,
            'portfolio': {},
            'inventory': [],
            'achievements': [],
            'transactions': [],
            'refs': 0,
            'ref_bonus': 0,
            'referrer': None,
            'last_trade': 0,
            'used_promos': []
        }
        save_user(user_id, user)
        return user

def save_user(user_id, data):
    with open(f'users/{user_id}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== КОМПАНИИ ==========
COMPANIES_FILE = 'companies.json'

def get_companies():
    data = load_json(COMPANIES_FILE)
    if not data:
        data = {
            'AAPL': {'name': 'Apple Inc.', 'price': 175.50, 'prev': 175.50},
            'MSFT': {'name': 'Microsoft', 'price': 330.25, 'prev': 330.25},
            'GOOG': {'name': 'Google', 'price': 2800.75, 'prev': 2800.75},
            'AMZN': {'name': 'Amazon', 'price': 3450.00, 'prev': 3450.00},
            'META': {'name': 'Meta', 'price': 310.80, 'prev': 310.80},
            'TSLA': {'name': 'Tesla', 'price': 240.50, 'prev': 240.50},
            'NVDA': {'name': 'NVIDIA', 'price': 890.60, 'prev': 890.60},
        }
        save_json(COMPANIES_FILE, data)
    return data

def save_companies(data):
    save_json(COMPANIES_FILE, data)

# ========== ПРОМОКОДЫ ==========
PROMO_FILE = 'promocodes.json'

def get_promos():
    return load_json(PROMO_FILE)

def save_promos(data):
    save_json(PROMO_FILE, data)

# ========== СЕЗОН ==========
SEASON_FILE = 'season.json'

def get_season():
    return load_json(SEASON_FILE)

def save_season(data):
    save_json(SEASON_FILE, data)

# ========== ДОСТИЖЕНИЯ ==========
ACHIEVEMENTS = {
    'first_trade': {'name': 'Первая сделка', 'emoji': '🎯', 'desc': 'Купи первые акции', 'reward': 500},
    'trader_10': {'name': 'Трейдер', 'emoji': '📊', 'desc': '10 сделок', 'reward': 1000},
    'trader_100': {'name': 'Профи', 'emoji': '📈', 'desc': '100 сделок', 'reward': 5000},
    'capital_10k': {'name': 'Инвестор', 'emoji': '💰', 'desc': 'Капитал 10,000$', 'reward': 2000},
    'capital_100k': {'name': 'Богач', 'emoji': '💎', 'desc': 'Капитал 100,000$', 'reward': 10000},
    'millionaire': {'name': 'Миллионер', 'emoji': '👑', 'desc': 'Капитал 1,000,000$', 'reward': 50000},
    'first_cube': {'name': 'Победитель', 'emoji': '🥇', 'desc': 'Получи кубок', 'reward': 3000},
    'ref_5': {'name': 'Лидер', 'emoji': '👥', 'desc': '5 рефералов', 'reward': 5000}
}

# ========== МАГАЗИН ==========
SHOP_ITEMS = {
    'booster': {'name': 'Ускоритель', 'desc': '🚀 Цены растут быстрее 24ч', 'price': 500, 'emoji': '🚀'},
    'shield': {'name': 'Страховка', 'desc': '🛡️ Защита от убытка', 'price': 300, 'emoji': '🛡️'},
    'analyst': {'name': 'Аналитик', 'desc': '📊 Прогноз цен', 'price': 200, 'emoji': '📊'},
    'random': {'name': 'Рандом', 'desc': '🎲 Бонус $50-500', 'price': 100, 'emoji': '🎲'},
    'vip': {'name': 'VIP', 'desc': '💎 +10% к доходу 30 дней', 'price': 5000, 'emoji': '💎'},
    'lucky': {'name': 'Лаки бокс', 'desc': '🎁 Случайный приз', 'price': 300, 'emoji': '🎁'}
}

# ========== КНОПКИ ==========
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="stats"),
        types.InlineKeyboardButton("📈 Компании", callback_data="list"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaders"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"),
        types.InlineKeyboardButton("🏆 Кубки", callback_data="cubes"),
        types.InlineKeyboardButton("👥 Рефералы", callback_data="ref"),
        types.InlineKeyboardButton("🎯 Достижения", callback_data="achs"),
        types.InlineKeyboardButton("💸 Перевод", callback_data="send"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    return markup

def back_kb():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="menu"))
    return markup

# ========== ПРОВЕРКА ==========
def check_user(user_id):
    if user_id != YOUR_ID:
        return False
    return True

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        bot.reply_to(message, "❌ Бот только для разработчика")
        return
    
    user = get_user(user_id)
    if message.from_user.username:
        user['username'] = message.from_user.username
    if message.from_user.first_name:
        user['name'] = message.from_user.first_name
    
    # Проверка реферала
    if len(message.text.split()) > 1:
        ref = message.text.split()[1]
        if ref.startswith('ref_'):
            try:
                ref_id = int(ref.replace('ref_', ''))
                if ref_id != user_id and not user['referrer']:
                    user['referrer'] = ref_id
                    ref_user = get_user(ref_id)
                    ref_user['refs'] += 1
                    ref_user['ref_bonus'] += 500
                    ref_user['money'] += 500
                    save_user(ref_id, ref_user)
                    user['money'] += 200
                    try:
                        bot.send_message(ref_id, f"🎉 Новый реферал! +500$")
                    except:
                        pass
            except:
                pass
    
    save_user(user_id, user)
    
    season = get_season()
    time_left = ""
    if season and season.get('active'):
        end = datetime.fromisoformat(season['end'])
        now = datetime.now()
        if now < end:
            delta = end - now
            time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
    
    text = f"👋 *Привет, {user['name'] or 'разработчик'}!*\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}\n📆 День: {user['day']}{time_left}"
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_menu())

# ========== СТАТУС ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    companies = get_companies()
    
    total = user['money']
    port_text = ""
    for t, a in user['portfolio'].items():
        price = companies.get(t, {}).get('price', 0)
        total += a * price
        port_text += f"• {t}: {a} шт. (${a*price:,.2f})\n"
    
    text = f"📊 *ТВОЯ СТАТИСТИКА*\n\n"
    text += f"💰 Деньги: ${user['money']:,.2f}\n"
    text += f"💵 Капитал: ${total:,.2f}\n"
    text += f"🏆 Кубков: {user['cubes']}\n"
    text += f"🛡️ Страховок: {user['shields']}\n"
    text += f"👥 Рефералов: {user['refs']}\n\n"
    
    if port_text:
        text += f"📋 *Портфель:*\n{port_text}"
    else:
        text += "📋 *Портфель:* Пусто"
    
    # Место в топе
    leaders = get_leaders(100)
    for i, u in enumerate(leaders, 1):
        if u['id'] == user_id:
            text += f"\n\n⭐ Место: {i} из {len(leaders)}"
            break
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КОМПАНИИ ==========
@bot.message_handler(commands=['list'])
def list_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    companies = get_companies()
    
    text = f"📋 *КОМПАНИИ (День {user['day']})*\n\n"
    for t, d in companies.items():
        change = ((d['price'] - d['prev']) / d['prev']) * 100
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        text += f"*{t}* — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change:+.2f}%\n\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПОКУПКА ==========
@bot.message_handler(commands=['buy'])
def buy_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /buy AAPL 5")
            return
        
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        companies = get_companies()
        if ticker not in companies:
            bot.reply_to(message, f"❌ Компания {ticker} не найдена")
            return
        
        user = get_user(user_id)
        price = companies[ticker]['price']
        total = price * amount
        
        if user['money'] < total:
            bot.reply_to(message, f"❌ Нужно ${total:,.2f}, у тебя ${user['money']:,.2f}")
            return
        
        user['money'] -= total
        user['portfolio'][ticker] = user['portfolio'].get(ticker, 0) + amount
        user['transactions'].append({'type': 'buy', 'ticker': ticker, 'amount': amount, 'price': price, 'time': str(datetime.now())})
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        # Проверка достижений
        check_achievements(user_id)
        
        bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ПРОДАЖА ==========
@bot.message_handler(commands=['sell'])
def sell_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /sell AAPL 5")
            return
        
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        companies = get_companies()
        if ticker not in companies:
            bot.reply_to(message, f"❌ Компания {ticker} не найдена")
            return
        
        user = get_user(user_id)
        if ticker not in user['portfolio'] or user['portfolio'][ticker] < amount:
            bot.reply_to(message, f"❌ У тебя только {user['portfolio'].get(ticker, 0)} акций")
            return
        
        price = companies[ticker]['price']
        total = price * amount
        
        user['money'] += total
        user['portfolio'][ticker] -= amount
        if user['portfolio'][ticker] == 0:
            del user['portfolio'][ticker]
        user['transactions'].append({'type': 'sell', 'ticker': ticker, 'amount': amount, 'price': price, 'time': str(datetime.now())})
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        # Проверка достижений
        check_achievements(user_id)
        
        bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== NEXT ==========
@bot.message_handler(commands=['next'])
def next_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    
    if user['last_trade'] < user['day']:
        bot.reply_to(message, "❌ Сначала купи или продай акции!")
        return
    
    companies = get_companies()
    news = []
    
    for ticker, data in list(companies.items()):
        # 5% шанс банкротства
        if random.random() < 0.05:
            news.append(f"💀 {data['name']} ОБАНКРОТИЛАСЬ! Акции сгорели!")
            
            # Удаляем у всех игроков
            for f in os.listdir('users'):
                if f.endswith('.json'):
                    u = get_user(int(f[:-5]))
                    if ticker in u['portfolio']:
                        del u['portfolio'][ticker]
                        save_user(u['id'], u)
            
            del companies[ticker]
            
            # Новая компания
            new_ticker = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
            new_name = f"{random.choice(['New', 'Tech', 'Global'])} {random.choice(['Corp', 'Inc', 'Ltd'])}"
            companies[new_ticker] = {'name': new_name, 'price': 1000.0, 'prev': 1000.0}
            news.append(f"✨ Новая компания {new_name} ({new_ticker}) появилась!")
        else:
            change = random.uniform(-0.1, 0.1)
            data['prev'] = data['price']
            data['price'] = round(data['price'] * (1 + change), 2)
    
    save_companies(companies)
    
    user['day'] += 1
    save_user(user_id, user)
    
    for n in news:
        bot.send_message(user_id, n)
    
    bot.reply_to(message, f"⏩ День {user['day']}! Цены обновлены.")

# ========== ЛИДЕРЫ ==========
def get_leaders(limit=10):
    users = []
    companies = get_companies()
    
    for f in os.listdir('users'):
        if f.endswith('.json'):
            u = get_user(int(f[:-5]))
            total = u['money']
            for t, a in u['portfolio'].items():
                total += a * companies.get(t, {}).get('price', 0)
            users.append({
                'id': u['id'],
                'name': u['name'] or u['username'] or f"User_{u['id']}",
                'total': round(total, 2),
                'cubes': u['cubes']
            })
    
    users.sort(key=lambda x: x['total'], reverse=True)
    return users[:limit]

@bot.message_handler(commands=['leaders'])
def leaders_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    leaders = get_leaders(10)
    season = get_season()
    
    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*"
    if season and season.get('active'):
        text += f"\nСезон: {season['name']}"
    text += "\n\n"
    
    for i, u in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {u['name'][:15]} — ${u['total']:,.2f} (🏆 {u['cubes']})\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== МАГАЗИН ==========
@bot.message_handler(commands=['shop'])
def shop_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    text = "🛒 *МАГАЗИН*\n\n"
    for item_id, item in SHOP_ITEMS.items():
        text += f"{item['emoji']} *{item['name']}* — ${item['price']}\n_{item['desc']}_\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for item_id, item in SHOP_ITEMS.items():
        markup.add(types.InlineKeyboardButton(
            f"{item['emoji']} {item['name']} ${item['price']}",
            callback_data=f"buy_{item_id}"
        ))
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="menu"))
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)

# ========== ИНВЕНТАРЬ ==========
@bot.message_handler(commands=['inv'])
def inv_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    
    text = "🎒 *ИНВЕНТАРЬ*\n\n"
    if user['inventory']:
        for i, item in enumerate(user['inventory'], 1):
            text += f"{i}. {item['emoji']} {item['name']}\n"
    else:
        text += "Пусто\n"
    
    text += f"\n🏆 Кубков: {user['cubes']}"
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КУБКИ ==========
@bot.message_handler(commands=['cubes'])
def cubes_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    
    text = f"🏆 *КУБКИ*\n\nВсего: {user['cubes']}\n\n"
    
    cubes = [i for i in user['inventory'] if i.get('type') == 'cube']
    if cubes:
        for c in cubes:
            text += f"• {c['name']}\n"
    else:
        text += "Нет кубков"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== РЕФЕРАЛЫ ==========
@bot.message_handler(commands=['ref'])
def ref_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"👥 *РЕФЕРАЛЫ*\n\n"
        f"🔗 Твоя ссылка:\n`{link}`\n\n"
        f"📊 Приглашено: {user['refs']}\n"
        f"💰 Заработано: ${user['ref_bonus']}\n\n"
        f"🎁 За друга +500$ тебе и +200$ другу!"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ДОСТИЖЕНИЯ ==========
def check_achievements(user_id):
    user = get_user(user_id)
    companies = get_companies()
    new_achs = []
    
    # Считаем сделки
    trades = len([t for t in user['transactions'] if t['type'] in ['buy', 'sell']])
    
    # Считаем капитал
    total = user['money']
    for t, a in user['portfolio'].items():
        total += a * companies.get(t, {}).get('price', 0)
    
    checks = [
        ('first_trade', trades >= 1),
        ('trader_10', trades >= 10),
        ('trader_100', trades >= 100),
        ('capital_10k', total >= 10000),
        ('capital_100k', total >= 100000),
        ('millionaire', total >= 1000000),
        ('first_cube', user['cubes'] >= 1),
        ('ref_5', user['refs'] >= 5)
    ]
    
    for ach_id, condition in checks:
        if condition and ach_id not in user['achievements']:
            user['achievements'].append(ach_id)
            user['money'] += ACHIEVEMENTS[ach_id]['reward']
            new_achs.append(ach_id)
    
    if new_achs:
        save_user(user_id, user)
        for ach in new_achs:
            info = ACHIEVEMENTS[ach]
            bot.send_message(user_id, 
                f"🔔 *Новое достижение!*\n{info['emoji']} {info['name']}\n+${info['reward']}", 
                parse_mode="Markdown")

@bot.message_handler(commands=['achs'])
def achs_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    user = get_user(user_id)
    
    text = "🎯 *ДОСТИЖЕНИЯ*\n\n"
    if user['achievements']:
        for ach in user['achievements']:
            info = ACHIEVEMENTS[ach]
            text += f"{info['emoji']} *{info['name']}*\n_{info['desc']}_\n\n"
    else:
        text += "Пока нет достижений"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПЕРЕВОД ==========
@bot.message_handler(commands=['send'])
def send_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /send @username 1000")
            return
        
        to_name = parts[1].replace('@', '')
        amount = int(parts[2])
        
        # Ищем получателя
        to_id = None
        for f in os.listdir('users'):
            if f.endswith('.json'):
                u = get_user(int(f[:-5]))
                if u['username'] and u['username'].lower() == to_name.lower():
                    to_id = u['id']
                    break
        
        if not to_id:
            bot.reply_to(message, f"❌ Пользователь @{to_name} не найден")
            return
        
        user = get_user(user_id)
        if user['money'] < amount:
            bot.reply_to(message, f"❌ Недостаточно средств. Нужно ${amount}")
            return
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        
        to_user = get_user(to_id)
        
        user['money'] -= amount
        to_user['money'] += amount
        
        user['transactions'].append({'type': 'send', 'to': to_id, 'amount': amount, 'time': str(datetime.now())})
        to_user['transactions'].append({'type': 'receive', 'from': user_id, 'amount': amount, 'time': str(datetime.now())})
        
        save_user(user_id, user)
        save_user(to_id, to_user)
        
        bot.reply_to(message, f"✅ Переведено ${amount} пользователю @{to_name}")
        
        try:
            bot.send_message(to_id, f"💰 Тебе перевели ${amount} от @{user['username'] or user['name']}")
        except:
            pass
        
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ПОМОЩЬ ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        return
    
    text = (
        "📚 *КОМАНДЫ*\n\n"
        "*👤 Для всех:*\n"
        "/start — главное меню\n"
        "/stats — статистика\n"
        "/list — список компаний\n"
        "/buy AAPL 5 — купить акции\n"
        "/sell AAPL 5 — продать акции\n"
        "/next — следующий день\n"
        "/leaders — таблица лидеров\n"
        "/shop — магазин\n"
        "/inv — инвентарь\n"
        "/cubes — кубки\n"
        "/send @user 1000 — перевод\n"
        "/ref — рефералы\n"
        "/achs — достижения\n"
        "/help — это меню\n\n"
        "*👑 Админ (только для тебя):*\n"
        "/admin stats — статистика бота\n"
        "/admin give ID 5000 — выдать деньги\n"
        "/admin take ID 2000 — забрать\n"
        "/admin cubes ID 3 — выдать кубки\n"
        "/admin reset ID — сброс\n"
        "/admin season ЛЕТО 14 — сезон"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        bot.reply_to(message, "❌ Только для разработчика")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        text = (
            "👑 *АДМИН-КОМАНДЫ*\n\n"
            "/admin stats — статистика\n"
            "/admin give ID 5000 — выдать деньги\n"
            "/admin take ID 2000 — забрать\n"
            "/admin cubes ID 3 — выдать кубки\n"
            "/admin reset ID — сброс\n"
            "/admin season ЛЕТО 14 — создать сезон"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
        return
    
    cmd = parts[1].lower()
    
    if cmd == "stats":
        users_count = len([f for f in os.listdir('users') if f.endswith('.json')])
        companies = get_companies()
        total_money = 0
        for f in os.listdir('users'):
            if f.endswith('.json'):
                u = get_user(int(f[:-5]))
                total_money += u['money']
        
        text = (
            f"📊 *СТАТИСТИКА БОТА*\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"🏢 Компаний: {len(companies)}\n"
            f"💰 Денег в игре: ${total_money:,.2f}"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
    
    elif cmd == "give" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        user = get_user(target)
        user['money'] += amount
        save_user(target, user)
        bot.reply_to(message, f"✅ Выдано ${amount} пользователю {target}")
    
    elif cmd == "take" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        user = get_user(target)
        user['money'] -= amount
        save_user(target, user)
        bot.reply_to(message, f"✅ Забрано ${amount} у {target}")
    
    elif cmd == "cubes" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        user = get_user(target)
        user['cubes'] += amount
        save_user(target, user)
        bot.reply_to(message, f"✅ Выдано {amount} кубков {target}")
    
    elif cmd == "reset" and len(parts) >= 3:
        target = int(parts[2])
        user = {
            'id': target,
            'name': None,
            'username': None,
            'money': 10000.0,
            'day': 1,
            'cubes': 0,
            'shields': 0,
            'portfolio': {},
            'inventory': [],
            'achievements': [],
            'transactions': [],
            'refs': 0,
            'ref_bonus': 0,
            'referrer': None,
            'last_trade': 0,
            'used_promos': []
        }
        save_user(target, user)
        bot.reply_to(message, f"✅ Пользователь {target} сброшен")
    
    elif cmd == "season" and len(parts) >= 4:
        name = parts[2]
        days = int(parts[3])
        season = {
            'name': name,
            'start': str(datetime.now()),
            'end': str(datetime.now() + timedelta(days=days)),
            'active': True
        }
        save_season(season)
        bot.reply_to(message, f"✅ Сезон '{name}' на {days} дней создан")

# ========== КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if user_id != YOUR_ID:
        bot.answer_callback_query(call.id, "❌ Не твой бот")
        return
    
    data = call.data
    
    if data == "menu":
        user = get_user(user_id)
        season = get_season()
        time_left = ""
        if season and season.get('active'):
            end = datetime.fromisoformat(season['end'])
            now = datetime.now()
            if now < end:
                delta = end - now
                time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
        
        text = f"👋 *Главное меню*\n\n💰 Баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}\n📆 День: {user['day']}{time_left}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                            parse_mode="Markdown", reply_markup=main_menu())
    
    elif data == "stats":
        stats_cmd(call.message)
    elif data == "list":
        list_cmd(call.message)
    elif data == "next":
        next_cmd(call.message)
    elif data == "leaders":
        leaders_cmd(call.message)
    elif data == "shop":
        shop_cmd(call.message)
    elif data == "inv":
        inv_cmd(call.message)
    elif data == "cubes":
        cubes_cmd(call.message)
    elif data == "ref":
        ref_cmd(call.message)
    elif data == "achs":
        achs_cmd(call.message)
    elif data == "send":
        bot.send_message(user_id, "💸 Используй: /send @username 1000")
    elif data == "help":
        help_cmd(call.message)
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        if item_id in SHOP_ITEMS:
            item = SHOP_ITEMS[item_id]
            user = get_user(user_id)
            
            if user['money'] < item['price']:
                bot.answer_callback_query(call.id, f"❌ Нужно ${item['price']}", show_alert=True)
                return
            
            user['money'] -= item['price']
            
            if item_id == 'lucky':
                chance = random.random()
                if chance < 0.3:
                    bonus = random.randint(100, 1000)
                    user['money'] += bonus
                    bot.answer_callback_query(call.id, f"🎁 +${bonus}!", show_alert=True)
                elif chance < 0.6:
                    rand_item = random.choice(['booster', 'shield', 'analyst'])
                    user['inventory'].append({
                        'type': rand_item,
                        'name': SHOP_ITEMS[rand_item]['name'],
                        'emoji': SHOP_ITEMS[rand_item]['emoji']
                    })
                    bot.answer_callback_query(call.id, f"🎁 Получен предмет!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, f"🎁 Ничего не выпало...", show_alert=True)
            else:
                user['inventory'].append({
                    'type': item_id,
                    'name': item['name'],
                    'emoji': item['emoji']
                })
                bot.answer_callback_query(call.id, f"✅ Куплен {item['emoji']} {item['name']}", show_alert=True)
            
            save_user(user_id, user)
            check_achievements(user_id)
    
    bot.answer_callback_query(call.id)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"👤 Твой ID: {YOUR_ID}")
    print("✅ Команды:")
    print("   /start, /stats, /list, /buy, /sell, /next")
    print("   /leaders, /shop, /inv, /cubes, /send, /ref, /achs, /help")
    print("   /admin - для админа")
    bot.infinity_polling()