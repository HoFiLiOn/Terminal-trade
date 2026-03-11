import telebot
from telebot import types
import json
import os
import random
from datetime import datetime

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
            'money': 10000.0,
            'day': 1,
            'cubes': 0,
            'portfolio': {},
            'inventory': [],
            'last_trade': 0
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
        }
        save_json('companies.json', data)
    return data

def save_companies(data):
    save_json('companies.json', data)

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
    
    # Только для тебя!
    if user_id != YOUR_ID:
        bot.reply_to(message, "❌ Бот только для разработчика")
        return
    
    user = get_user(user_id)
    if message.from_user.first_name:
        user['name'] = message.from_user.first_name
    save_user(user_id, user)
    
    text = f"👋 *Привет!*\n\n💰 Баланс: ${user['money']:,.2f}\n📆 День: {user['day']}"
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_menu())

# ========== СТАТУС ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    user = get_user(user_id)
    total = user['money']
    companies = get_companies()
    
    for t, a in user['portfolio'].items():
        total += a * companies.get(t, {}).get('price', 0)
    
    text = f"📊 *Статус*\n\n💰 Деньги: ${user['money']:,.2f}\n💵 Капитал: ${total:,.2f}\n🏆 Кубков: {user['cubes']}"
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КОМПАНИИ ==========
@bot.message_handler(commands=['list'])
def list_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    user = get_user(user_id)
    companies = get_companies()
    
    text = f"📋 *Компании (День {user['day']})*\n\n"
    for t, d in companies.items():
        change = ((d['price'] - d['prev']) / d['prev']) * 100
        emoji = "🟢" if change > 0 else "🔴"
        text += f"*{t}* — {d['name']}\n💰 ${d['price']:,.2f} {emoji} {change:+.2f}%\n\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПОКУПКА ==========
@bot.message_handler(commands=['buy'])
def buy_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        companies = get_companies()
        if ticker not in companies:
            bot.reply_to(message, "❌ Нет такой компании")
            return
        
        user = get_user(user_id)
        price = companies[ticker]['price']
        total = price * amount
        
        if user['money'] < total:
            bot.reply_to(message, f"❌ Нужно ${total}")
            return
        
        user['money'] -= total
        user['portfolio'][ticker] = user['portfolio'].get(ticker, 0) + amount
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total}")
        
    except:
        bot.reply_to(message, "❌ /buy AAPL 5")

# ========== ПРОДАЖА ==========
@bot.message_handler(commands=['sell'])
def sell_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        companies = get_companies()
        user = get_user(user_id)
        
        if ticker not in user['portfolio'] or user['portfolio'][ticker] < amount:
            bot.reply_to(message, f"❌ У тебя {user['portfolio'].get(ticker,0)} акций")
            return
        
        price = companies[ticker]['price']
        total = price * amount
        
        user['money'] += total
        user['portfolio'][ticker] -= amount
        if user['portfolio'][ticker] == 0:
            del user['portfolio'][ticker]
        user['last_trade'] = user['day']
        save_user(user_id, user)
        
        bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${total}")
        
    except:
        bot.reply_to(message, "❌ /sell AAPL 5")

# ========== NEXT ==========
@bot.message_handler(commands=['next'])
def next_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    user = get_user(user_id)
    
    if user['last_trade'] < user['day']:
        bot.reply_to(message, "❌ Сначала купи/продай акции!")
        return
    
    companies = get_companies()
    
    for t, d in companies.items():
        change = random.uniform(-0.1, 0.1)
        d['prev'] = d['price']
        d['price'] = round(d['price'] * (1 + change), 2)
    
    save_companies(companies)
    
    user['day'] += 1
    save_user(user_id, user)
    
    bot.reply_to(message, f"⏩ День {user['day']}! Цены обновлены.")

# ========== ЛИДЕРЫ ==========
@bot.message_handler(commands=['leaders'])
def leaders_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    users = []
    for f in os.listdir('users'):
        if f.endswith('.json'):
            u = get_user(int(f[:-5]))
            total = u['money']
            companies = get_companies()
            for t, a in u['portfolio'].items():
                total += a * companies.get(t, {}).get('price', 0)
            users.append({'name': u['name'] or f"User_{u['id']}", 'total': total})
    
    users.sort(key=lambda x: x['total'], reverse=True)
    
    text = "🏆 *Топ игроков*\n\n"
    for i, u in enumerate(users[:5], 1):
        text += f"{i}. {u['name'][:15]} — ${u['total']:,.2f}\n"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== ПОМОЩЬ ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    if user_id != YOUR_ID:
        return
    
    text = (
        "📚 *Команды*\n\n"
        "/buy AAPL 5 — купить\n"
        "/sell AAPL 5 — продать\n"
        "/next — след день\n"
        "/stats — статус\n"
        "/list — компании\n"
        "/leaders — топ"
    )
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========== КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if user_id != YOUR_ID:
        bot.answer_callback_query(call.id, "❌ Не твой бот")
        return
    
    if call.data == "menu":
        user = get_user(user_id)
        text = f"👋 *Главное*\n\n💰 Баланс: ${user['money']:,.2f}\n📆 День: {user['day']}"
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
print("🚀 Бот запущен для одного пользователя")
print(f"👤 Твой ID: {YOUR_ID}")
bot.infinity_polling()