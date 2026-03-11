import telebot
from telebot import types
import json
import os
import random
from datetime import datetime, timedelta

# ========== ТВОИ ДАННЫЕ ==========
TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
YOUR_ID = 7040677455  # Твой ID
ADMIN_ID = 8388843828 # Админ

START_MONEY = 10000.0

# ========== ФАЙЛЫ ==========
os.makedirs('users', exist_ok=True)

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
            'username': None,
            'name': None,
            'money': START_MONEY,
            'day': 1,
            'cubes': 0,
            'shields': 0,
            'portfolio': {},
            'inventory': [],
            'achievements': [],
            'transactions': [],
            'refs': 0,
            'ref_bonus': 0,
            'last_trade': 0,
            'joined': str(datetime.now())
        }
        save_user(user_id, user)
        return user

def save_user(user_id, data):
    with open(f'users/{user_id}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== КОМПАНИИ ==========
def get_companies():
    data = load_json('companies.json')
    if not data:
        data = {
            'AAPL': {'name': 'Apple', 'price': 175.50, 'prev': 175.50},
            'MSFT': {'name': 'Microsoft', 'price': 330.25, 'prev': 330.25},
            'GOOG': {'name': 'Google', 'price': 2800.75, 'prev': 2800.75},
            'AMZN': {'name': 'Amazon', 'price': 3450.00, 'prev': 3450.00},
            'META': {'name': 'Meta', 'price': 310.80, 'prev': 310.80},
        }
        save_json('companies.json', data)
    return data

def save_companies(data):
    save_json('companies.json', data)

# ========== БОТ ==========
bot = telebot.TeleBot(TOKEN)

# ========== КНОПКИ ==========
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="stats"),
        types.InlineKeyboardButton("📈 Компании", callback_data="list"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaders"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    return markup

def back_kb():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="menu"))
    return markup

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    
    # Только для тебя и админа
    if user_id != YOUR_ID and user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Бот только для разработчика")
        return
    
    user = get_user(user_id)
    if message.from_user.username:
        user['username'] = message.from_user.username
    if message.from_user.first_name:
        user['name'] = message.from_user.first_name
    save_user(user_id, user)
    
    text = (
        f"👋 *Привет, {user['name'] or 'разработчик'}!*\n\n"
        f"💰 Баланс: ${user['money']:,.2f}\n"
        f"🏆 Кубков: {user['cubes']}\n"
        f"📆 День: {user['day']}"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_menu())

# ========== СТАТУС ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    total = user['money']
    port_text = ""
    companies = get_companies()
    
    for ticker, amount in user['portfolio'].items():
        price = companies.get(ticker, {}).get('price', 0)
        total += amount * price
        port_text += f"• {ticker}: {amount} шт. (${amount*price:,.2f})\n"
    
    text = f"📊 *ТВОЯ СТАТИСТИКА*\n\n"
    text += f"💰 Деньги: ${user['money']:,.2f}\n"
    text += f"💵 Капитал: ${total:,.2f}\n"
    text += f"🏆 Кубков: {user['cubes']}\n"
    text += f"🛡️ Страховок: {user['shields']}\n\n"
    
    if port_text:
        text += f"📋 *Портфель:*\n{port_text}"
    else:
        text += "📋 *Портфель:* Пусто"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КОМПАНИИ ==========
@bot.message_handler(commands=['list'])
def list_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    companies = get_companies()
    
    text = f"📋 *КОМПАНИИ (День {user['day']})*\n\n"
    for ticker, data in companies.items():
        change = ((data['price'] - data['prev']) / data['prev']) * 100
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        text += f"*{ticker}* — {data['name']}\n"
        text += f"💰 ${data['price']:,.2f} {emoji} {change:+.2f}%\n\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПОКУПКА ==========
@bot.message_handler(commands=['buy'])
def buy_cmd(message):
    user_id = message.from_user.id
    
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
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ПРОДАЖА ==========
@bot.message_handler(commands=['sell'])
def sell_cmd(message):
    user_id = message.from_user.id
    
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
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${total:,.2f}")
        
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== NEXT ==========
@bot.message_handler(commands=['next'])
def next_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if user['last_trade'] < user['day']:
        bot.reply_to(message, "❌ Сначала купи или продай акции!")
        return
    
    companies = get_companies()
    news = []
    
    for ticker, data in list(companies.items()):
        if random.random() < 0.05:
            news.append(f"💀 {data['name']} обанкротилась!")
            del companies[ticker]
            
            # Новая компания
            new_ticker = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
            new_name = f"New {random.choice(['Tech', 'Corp', 'Inc'])}"
            companies[new_ticker] = {'name': new_name, 'price': 1000.0, 'prev': 1000.0}
            news.append(f"✨ Новая компания {new_name} появилась!")
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
@bot.message_handler(commands=['leaders'])
def leaders_cmd(message):
    user_id = message.from_user.id
    
    users = []
    for f in os.listdir('users'):
        if f.endswith('.json'):
            u = get_user(int(f[:-5]))
            total = u['money']
            companies = get_companies()
            for t, a in u['portfolio'].items():
                total += a * companies.get(t, {}).get('price', 0)
            users.append({
                'name': u['name'] or f"User_{u['id']}",
                'total': total,
                'cubes': u['cubes']
            })
    
    users.sort(key=lambda x: x['total'], reverse=True)
    
    text = "🏆 *ТОП ИГРОКОВ*\n\n"
    for i, u in enumerate(users[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {u['name'][:15]} — ${u['total']:,.2f} (🏆 {u['cubes']})\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПОМОЩЬ ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = (
        "📚 *ПОМОЩЬ*\n\n"
        "/buy AAPL 5 — купить акции\n"
        "/sell AAPL 5 — продать акции\n"
        "/next — следующий день\n"
        "/stats — статистика\n"
        "/list — список компаний\n"
        "/leaders — таблица лидеров\n"
        "/start — главное меню"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    
    if call.data == "menu":
        user = get_user(user_id)
        text = f"👋 *Главное меню*\n\n💰 Баланс: ${user['money']:,.2f}\n📆 День: {user['day']}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                            parse_mode="Markdown", reply_markup=main_menu())
    
    elif call.data == "stats":
        stats_cmd(call.message)
    
    elif call.data == "list":
        list_cmd(call.message)
    
    elif call.data == "next":
        next_cmd(call.message)
    
    elif call.data == "leaders":
        leaders_cmd(call.message)
    
    elif call.data == "help":
        help_cmd(call.message)
    
    bot.answer_callback_query(call.id)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот запущен для разработчика")
    print(f"👤 Твой ID: {YOUR_ID}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()