import telebot
from telebot import types
import random
import json
import os
from datetime import datetime
from flask import Flask
import threading

# ========== ТОКЕН ==========
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ========== ФАЙЛЫ БАЗЫ ДАННЫХ ==========
USERS_DIR = "users"  # Папка для файлов игроков
LEADERBOARD_FILE = "leaderboard.json"

# Создаем папку для пользователей, если её нет
if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

# ========== ДАННЫЕ ПО УМОЛЧАНИЮ ==========
DEFAULT_COMPANIES = {
    'AAPL': {'name': 'Apple Inc.', 'price': 175.50},
    'MSFT': {'name': 'Microsoft Corp.', 'price': 330.25},
    'GOOG': {'name': 'Alphabet (Google)', 'price': 2800.75},
    'AMZN': {'name': 'Amazon.com Inc.', 'price': 3450.00},
    'TSLA': {'name': 'Tesla Inc.', 'price': 900.50},
    'META': {'name': 'Meta Platforms', 'price': 310.80},
    'NVDA': {'name': 'NVIDIA Corp.', 'price': 890.60},
    'JPM': {'name': 'JPMorgan Chase', 'price': 150.30},
    'JNJ': {'name': 'Johnson & Johnson', 'price': 160.40},
    'WMT': {'name': 'Walmart Inc.', 'price': 145.20}
}

# ========== ВЕБ-СЕРВЕР ДЛЯ RAILWAY ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run_web, daemon=True).start()

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ИГРОКАМИ ==========
def get_user_file(user_id):
    """Возвращает путь к файлу игрока"""
    return os.path.join(USERS_DIR, f"{user_id}.json")

def load_user(user_id):
    """Загружает данные конкретного игрока"""
    user_file = get_user_file(user_id)
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Новый игрок
        return {
            'money': 1000.0,
            'portfolio': {},
            'day': 1,
            'companies': DEFAULT_COMPANIES.copy(),
            'username': None,
            'first_seen': str(datetime.now())
        }

def save_user(user_id, data):
    """Сохраняет данные игрока"""
    user_file = get_user_file(user_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Обновляем таблицу лидеров
    update_leaderboard(user_id, data)

# ========== ТАБЛИЦА ЛИДЕРОВ ==========
def load_leaderboard():
    """Загружает общую таблицу лидеров"""
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def calculate_total_capital(user_data):
    """Считает общий капитал игрока (деньги + акции)"""
    total = user_data['money']
    for ticker, amount in user_data['portfolio'].items():
        total += amount * user_data['companies'][ticker]['price']
    return round(total, 2)

def update_leaderboard(user_id, user_data):
    """Обновляет таблицу лидеров"""
    leaderboard = load_leaderboard()
    
    capital = calculate_total_capital(user_data)
    username = user_data.get('username') or f"Player_{user_id}"
    
    # Ищем игрока в таблице
    found = False
    for entry in leaderboard:
        if entry['user_id'] == user_id:
            # Обновляем только если капитал вырос
            if capital > entry['capital']:
                entry['capital'] = capital
                entry['day'] = user_data['day']
                entry['last_update'] = str(datetime.now())
            found = True
            break
    
    # Если игрок не найден, добавляем
    if not found:
        leaderboard.append({
            'user_id': user_id,
            'username': username,
            'capital': capital,
            'day': user_data['day'],
            'first_seen': user_data.get('first_seen', str(datetime.now())),
            'last_update': str(datetime.now())
        })
    
    # Сортируем по капиталу (от большего к меньшему)
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    
    # Сохраняем
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, indent=2, ensure_ascii=False)

def get_leaderboard_text():
    """Возвращает красивое отображение таблицы лидеров"""
    leaderboard = load_leaderboard()
    
    if not leaderboard:
        return "🏆 Таблица лидеров пока пуста. Играй и стань первым!"
    
    text = "🏆 **ГЛОБАЛЬНАЯ ТАБЛИЦА ЛИДЕРОВ**\n\n"
    text += "Рейтинг всех трейдеров по капиталу:\n\n"
    
    for i, entry in enumerate(leaderboard[:10], 1):
        # Медальки для топ-3
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = "📊"
        
        # Имя (обрезаем если длинное)
        name = entry['username']
        if len(name) > 15:
            name = name[:12] + "..."
        
        text += f"{medal} **{i}.** {name}\n"
        text += f"   💰 ${entry['capital']:,.2f} | 📅 День {entry['day']}\n"
    
    # Добавляем статистику
    total_players = len(leaderboard)
    text += f"\n👥 Всего трейдеров: {total_players}"
    
    return text

# ========== ФУНКЦИИ ИГРЫ ==========
def change_prices(user_data):
    """Изменение цен для конкретного игрока"""
    for ticker in user_data['companies']:
        change = random.uniform(-0.05, 0.05)
        user_data['companies'][ticker]['price'] *= (1 + change)
        user_data['companies'][ticker]['price'] = round(user_data['companies'][ticker]['price'], 2)

def buy_stock(user_data, ticker, amount):
    """Покупка акций"""
    if ticker not in user_data['companies']:
        return False, "❌ Нет такой компании"
    
    price = user_data['companies'][ticker]['price']
    total = price * amount
    
    if user_data['money'] >= total:
        user_data['money'] -= total
        if ticker in user_data['portfolio']:
            user_data['portfolio'][ticker] += amount
        else:
            user_data['portfolio'][ticker] = amount
        return True, f"✅ Куплено {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"❌ Недостаточно денег. Нужно ${total:,.2f}"

def sell_stock(user_data, ticker, amount):
    """Продажа акций"""
    if ticker not in user_data['portfolio']:
        return False, "❌ У вас нет таких акций"
    
    if user_data['portfolio'][ticker] >= amount:
        price = user_data['companies'][ticker]['price']
        total = price * amount
        user_data['money'] += total
        user_data['portfolio'][ticker] -= amount
        
        if user_data['portfolio'][ticker] == 0:
            del user_data['portfolio'][ticker]
        
        return True, f"✅ Продано {amount} {ticker} за ${total:,.2f}"
    else:
        return False, f"❌ У вас только {user_data['portfolio'][ticker]} акций"

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📊 Мой статус")
    btn2 = types.KeyboardButton("📈 Список компаний")
    btn3 = types.KeyboardButton("⏩ Следующий день")
    btn4 = types.KeyboardButton("🏆 Таблица лидеров")
    btn5 = types.KeyboardButton("🔄 Новая игра")
    btn6 = types.KeyboardButton("❓ Помощь")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    # Загружаем или создаем игрока
    user_data = load_user(user_id)
    user_data['username'] = username
    save_user(user_id, user_data)
    
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
║    Биржевой симулятор в TG    ║
╚══════════════════════════════╝

Привет, {username}! 👋

📋 **Как играть:**
• У каждого игрока своя игра
• Цены меняются каждый день
• Таблица лидеров общая для всех

💰 **Стартовый капитал:** $1000

🎮 **Используй кнопки внизу экрана**
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['leaderboard'])
def leaderboard_command(message):
    text = get_leaderboard_text()
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    capital = calculate_total_capital(user_data)
    
    text = f"""
📊 **ТВОЙ СТАТУС** (День {user_data['day']})

💰 Баланс: ${user_data['money']:,.2f}
📈 Активы: ${capital - user_data['money']:,.2f}
💵 Общий капитал: ${capital:,.2f}

📋 **Портфель:**
    """
    
    if user_data['portfolio']:
        for ticker, amount in user_data['portfolio'].items():
            price = user_data['companies'][ticker]['price']
            value = amount * price
            text += f"\n{ticker}: {amount} шт. (${value:,.2f})"
    else:
        text += "\nУ вас пока нет акций"
    
    # Показываем место в лидерборде
    leaderboard = load_leaderboard()
    for i, entry in enumerate(leaderboard, 1):
        if entry['user_id'] == user_id:
            text += f"\n\n🏆 Твое место: **{i}** из {len(leaderboard)}"
            break
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['list'])
def list_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    text = f"📋 **ВСЕ КОМПАНИИ** (День {user_data['day']})\n\n"
    for ticker, data in user_data['companies'].items():
        text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f}\n\n"
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['next'])
def next_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    change_prices(user_data)
    user_data['day'] += 1
    save_user(user_id, user_data)
    
    text = f"⏩ **День {user_data['day']}**\n\n✅ Цены обновлены!"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['reset'])
def reset_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    # Сохраняем старые данные для истории (можно потом добавить)
    user_data = {
        'money': 1000.0,
        'portfolio': {},
        'day': 1,
        'companies': DEFAULT_COMPANIES.copy(),
        'username': username,
        'first_seen': str(datetime.now())
    }
    save_user(user_id, user_data)
    
    text = "🔄 **Новая игра!**\nТы начинаешь заново с $1000"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ========== ОБРАБОТКА КНОПОК ==========
@bot.message_handler(func=lambda message: message.text in ["📊 Мой статус", "📈 Список компаний", "⏩ Следующий день", "🏆 Таблица лидеров", "🔄 Новая игра", "❓ Помощь"])
def button_handler(message):
    if message.text == "📊 Мой статус":
        status_command(message)
    elif message.text == "📈 Список компаний":
        list_command(message)
    elif message.text == "⏩ Следующий день":
        next_command(message)
    elif message.text == "🏆 Таблица лидеров":
        leaderboard_command(message)
    elif message.text == "🔄 Новая игра":
        reset_command(message)
    elif message.text == "❓ Помощь":
        help_command(message)

# ========== ОБРАБОТКА ПОКУПКИ/ПРОДАЖИ ==========
@bot.message_handler(func=lambda message: message.text.lower().startswith(('buy ', 'sell ')))
def trade_command(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    
    try:
        parts = message.text.split()
        command = parts[0].lower()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        if command == 'buy':
            success, msg = buy_stock(user_data, ticker, amount)
        elif command == 'sell':
            success, msg = sell_stock(user_data, ticker, amount)
        else:
            bot.send_message(message.chat.id, "❌ Неизвестная команда", reply_markup=main_menu())
            return
        
        if success:
            save_user(user_id, user_data)
        
        bot.send_message(message.chat.id, msg, reply_markup=main_menu())
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Формат: buy AAPL 5 или sell TSLA 2", reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
📚 ПОМОЩЬ

🎮 **Кнопки:**
• Мой статус — баланс и портфель
• Список компаний — все цены
• Следующий день — новый торговый день
• Таблица лидеров — рейтинг всех игроков
• Новая игра — начать заново

⌨️ Команды:
buy AAPL 5 — купить 5 акций Apple
sell TSLA 2 — продать 2 акции Tesla

🏆 Таблица лидеров:
Обновляется автоматически. Соревнуйся с другими игроками!
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    bot.send_message(message.chat.id, "❌ Неизвестная команда. Используй кнопки или /help", reply_markup=main_menu())

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот Terminal Trader с глобальной таблицей лидеров запущен...")
    bot.infinity_polling()