import telebot
import random
import json
import os
from datetime import datetime
from flask import Flask
import threading

# ========== ТОКЕН ==========
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ========== ФАЙЛ БАЗЫ ДАННЫХ ==========
DATA_FILE = "trader_data.json"

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

# Запускаем веб-сервер в отдельном потоке
threading.Thread(target=run_web, daemon=True).start()

# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ==========
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

# Загружаем сохранение
load_game()

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

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    text = """
╔══════════════════════════════╗
║     TERMINAL TRADER BOT      ║
║    Биржевой симулятор в TG    ║
╚══════════════════════════════╝

📋 **Как играть:**
У вас есть $1000 стартового капитала.
Цены меняются каждый день.

🎮 **Команды:**
/status — баланс и портфель
/list — все компании
/next — следующий день
buy ТИКЕР КОЛИЧЕСТВО — купить
sell ТИКЕР КОЛИЧЕСТВО — продать
/help — справка

💡 **Пример:** buy AAPL 5
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
📚 **ПОЛНАЯ СПРАВКА**

/status — баланс, портфель, капитал
/list — все компании с ценами
/next — следующий день
buy ТИКЕР КОЛИЧЕСТВО — купить
sell ТИКЕР КОЛИЧЕСТВО — продать

**Тикеры:** AAPL, MSFT, GOOG, AMZN, TSLA, META, NVDA, JPM, JNJ, WMT
    """
    bot.reply_to(message, text)

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
    bot.reply_to(message, text)

@bot.message_handler(commands=['list'])
def list_command(message):
    text = f"📋 **ВСЕ КОМПАНИИ** (День {day})\n\n"
    for ticker, data in companies.items():
        text += f"{ticker} — {data['name']}\n💰 ${data['price']:,.2f}\n\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['next'])
def next_command(message):
    global day
    change_prices()
    day += 1
    save_game()
    text = f"⏩ **День {day}**\n\nЦены обновлены!\n/list — посмотреть цены"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: message.text.startswith('buy '))
def buy_command(message):
    global money
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        if ticker not in companies:
            bot.reply_to(message, "❌ Нет такой компании")
            return
        
        price = companies[ticker]['price']
        total = price * amount
        
        if money >= total:
            money -= total
            if ticker in portfolio:
                portfolio[ticker] += amount
            else:
                portfolio[ticker] = amount
            save_game()
            bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        else:
            bot.reply_to(message, f"❌ Недостаточно денег. Нужно ${total:,.2f}")
    except:
        bot.reply_to(message, "❌ Формат: buy AAPL 5")

@bot.message_handler(func=lambda message: message.text.startswith('sell '))
def sell_command(message):
    global money
    try:
        parts = message.text.split()
        ticker = parts[1].upper()
        amount = int(parts[2])
        
        if ticker not in portfolio:
            bot.reply_to(message, "❌ У вас нет таких акций")
            return
        
        if portfolio[ticker] >= amount:
            price = companies[ticker]['price']
            money += price * amount
            portfolio[ticker] -= amount
            
            if portfolio[ticker] == 0:
                del portfolio[ticker]
            
            save_game()
            bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${price * amount:,.2f}")
        else:
            bot.reply_to(message, f"❌ У вас только {portfolio[ticker]} акций")
    except:
        bot.reply_to(message, "❌ Формат: sell AAPL 2")

@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    bot.reply_to(message, "❌ Неизвестная команда. Введи /help")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот Terminal Trader запущен на Railway...")
    bot.infinity_polling()