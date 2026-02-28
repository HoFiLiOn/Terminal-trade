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
DATA_FILE = "trader_data.json"
LEADERBOARD_FILE = "leaderboard.json"

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

# ========== ИНИЦИАЛИЗАЦИЯ ==========
money = 1000.0
portfolio = {}
day = 1
companies = DEFAULT_COMPANIES.copy()

# ========== ВЕБ-СЕРВЕР ДЛЯ RAILWAY ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run_web, daemon=True).start()

# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ИГРЫ ==========
def load_game():
    global money, portfolio, day, companies
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        money = data['money']
        portfolio = data['portfolio']
        day = data['day']
        for ticker, price_data in data['companies'].items():
            if ticker in companies:
                companies[ticker]['price'] = price_data['price']

def save_game():
    data = {
        'money': money,
        'portfolio': portfolio,
        'day': day,
        'companies': {
            ticker: {'price': data['price']} 
            for ticker, data in companies.items()
        },
        'last_update': str(datetime.now())
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== ТАБЛИЦА ЛИДЕРОВ ==========
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_to_leaderboard(user_id, username, capital, days):
    leaderboard = load_leaderboard()
    
    # Добавляем новую запись
    leaderboard.append({
        'user_id': user_id,
        'username': username or f"User_{user_id}",
        'capital': round(capital, 2),
        'days': days,
        'date': str(datetime.now())
    })
    
    # Сортируем по капиталу (от большего к меньшему)
    leaderboard.sort(key=lambda x: x['capital'], reverse=True)
    
    # Оставляем только топ-10
    leaderboard = leaderboard[:10]
    
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, indent=2, ensure_ascii=False)

def get_leaderboard_text():
    leaderboard = load_leaderboard()
    if not leaderboard:
        return "🏆 Таблица лидеров пока пуста. Будь первым!"
    
    text = "🏆 **ТОП-10 ТРЕЙДЕРОВ**\n\n"
    for i, entry in enumerate(leaderboard, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
        text += f"{medal} {i}. {entry['username']}\n"
        text += f"   💰 ${entry['capital']:,.2f} | 📅 {entry['days']} дней\n"
    
    return text

# ========== ФУНКЦИИ ИГРЫ ==========
def change_prices():
    for ticker in companies:
        change = random.uniform(-0.05, 0.05)
        companies[ticker]['price'] *= (1 + change)
        companies[ticker]['price'] = round(companies[ticker]['price'], 2)

def get_total_capital():
    total = money
    for ticker, amount in portfolio.items():
        total += amount * companies[ticker]['price']
    return total

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📊 Статус")
    btn2 = types.KeyboardButton("📈 Список компаний")
    btn3 = types.KeyboardButton("⏩ Следующий день")
    btn4 = types.KeyboardButton("🏆 Лидеры")
    btn5 = types.KeyboardButton("🔄 Сброс")
    btn6 = types.KeyboardButton("❓ Помощь")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    username = message.from_user.first_name or message.from_user.username
    text = f"""
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
║    Биржевой симулятор в TG    ║
╚══════════════════════════════╝

Привет, {username}! 👋

📋 **Как играть:**
У вас есть $1000 стартового капитала.
Цены меняются каждый день.

💡 **Используй кнопки внизу экрана**
или вводи команды вручную.

🎮 **Команды:**
buy AAPL 5 — купить 5 акций Apple
sell TSLA 2 — продать 2 акции Tesla
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
📚 **ПОЛНАЯ СПРАВКА**

📊 **Кнопки:**
• Статус — баланс и портфель
• Список компаний — все цены
• Следующий день — новый торговый день
• Лидеры — таблица рекордов
• Сброс — начать игру заново

⌨️ **Ручные команды:**
buy ТИКЕР КОЛИЧЕСТВО — купить
sell ТИКЕР КОЛИЧЕСТВО — продать

📈 **Тикеры:** AAPL, MSFT, GOOG, AMZN, TSLA, META, NVDA, JPM, JNJ, WMT

💡 **Пример:** buy AAPL 5
    """
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['status'])
def status_command(message):
    total = get_total_capital()
    text = f"""
📊 **СТАТУС** (День {day})

💰 Баланс: ${money:,.2f}
💵 Общий капитал: ${total:,.2f}

📋 **Портфель:**
    """
    if portfolio:
        for ticker, amount in portfolio.items():
            price = companies[ticker]['price']
            value = amount * price
            text += f"\n{ticker}: {amount} шт. (${value:,.2f})"
    else:
        text += "\nУ вас пока нет акций"
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['list'])
def list_command(message):
    text = f"📋 **ВСЕ КОМПАНИИ** (День {day})\n\n"
    for ticker, data in companies.items():
        text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f}\n\n"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['next'])
def next_command(message):
    global day
    change_prices()
    day += 1
    save_game()
    
    # Показываем топ-3 изменения цен
    changes = []
    for ticker, data in companies.items():
        changes.append((ticker, data['price']))
    
    text = f"⏩ **День {day}**\n\n✅ Цены обновлены!\n📌 Используй /list для просмотра"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['leaderboard'])
def leaderboard_command(message):
    text = get_leaderboard_text()
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['reset'])
def reset_command(message):
    global money, portfolio, day, companies
    
    # Сохраняем результат перед сбросом
    total = get_total_capital()
    username = message.from_user.username or message.from_user.first_name or "Player"
    save_to_leaderboard(message.from_user.id, username, total, day)
    
    # Сбрасываем игру
    money = 1000.0
    portfolio = {}
    day = 1
    companies = DEFAULT_COMPANIES.copy()
    save_game()
    
    text = "🔄 **Игра сброшена!**\nТвой результат сохранён в таблице лидеров.\nТы начинаешь заново с $1000"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ========== ОБРАБОТКА КНОПОК ==========
@bot.message_handler(func=lambda message: message.text in ["📊 Статус", "📈 Список компаний", "⏩ Следующий день", "🏆 Лидеры", "🔄 Сброс", "❓ Помощь"])
def button_handler(message):
    if message.text == "📊 Статус":
        status_command(message)
    elif message.text == "📈 Список компаний":
        list_command(message)
    elif message.text == "⏩ Следующий день":
        next_command(message)
    elif message.text == "🏆 Лидеры":
        leaderboard_command(message)
    elif message.text == "🔄 Сброс":
        reset_command(message)
    elif message.text == "❓ Помощь":
        help_command(message)

# ========== ОБРАБОТКА ПОКУПКИ/ПРОДАЖИ ==========
@bot.message_handler(func=lambda message: message.text.lower().startswith(('buy ', 'sell ')))
def trade_command(message):
    global money
    try:
        parts = message.text.split()
        command = parts[0].lower()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        if ticker not in companies:
            bot.send_message(message.chat.id, "❌ Нет такой компании", reply_markup=main_menu())
            return
        
        if command == 'buy':
            price = companies[ticker]['price']
            total = price * amount
            
            if money >= total:
                money -= total
                if ticker in portfolio:
                    portfolio[ticker] += amount
                else:
                    portfolio[ticker] = amount
                save_game()
                bot.send_message(message.chat.id, f"✅ Куплено {amount} {ticker} за ${total:,.2f}", reply_markup=main_menu())
            else:
                bot.send_message(message.chat.id, f"❌ Недостаточно денег. Нужно ${total:,.2f}", reply_markup=main_menu())
        
        elif command == 'sell':
            if ticker not in portfolio:
                bot.send_message(message.chat.id, "❌ У вас нет таких акций", reply_markup=main_menu())
                return
            
            if portfolio[ticker] >= amount:
                price = companies[ticker]['price']
                money += price * amount
                portfolio[ticker] -= amount
                
                if portfolio[ticker] == 0:
                    del portfolio[ticker]
                
                save_game()
                bot.send_message(message.chat.id, f"✅ Продано {amount} {ticker} за ${price * amount:,.2f}", reply_markup=main_menu())
            else:
                bot.send_message(message.chat.id, f"❌ У вас только {portfolio[ticker]} акций", reply_markup=main_menu())
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Формат: buy AAPL 5 или sell TSLA 2", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    bot.send_message(message.chat.id, "❌ Неизвестная команда. Используй кнопки или /help", reply_markup=main_menu())

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    load_game()
    print("🤖 Бот Terminal Trader с кнопками запущен на Railway...")
    bot.infinity_polling()