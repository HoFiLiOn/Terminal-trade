import telebot
from telebot import types
import random
from datetime import datetime, timedelta

from config import TOKEN, ADMINS, IMAGES, START_MONEY, STORY
import database
import utils

bot = telebot.TeleBot(TOKEN)

# Инициализация БД
database.init_database()

# ========== КНОПКИ ==========

def main_menu_kb():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статус", callback_data="stats"),
        types.InlineKeyboardButton("📈 Компании", callback_data="companies"),
        types.InlineKeyboardButton("⏩ Next", callback_data="next"),
        types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🏆 Кубки", callback_data="cubes"),
        types.InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
        types.InlineKeyboardButton("🎯 Достижения", callback_data="achievements"),
        types.InlineKeyboardButton("💸 Перевести", callback_data="transfer"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    return markup

def back_kb(target):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data=target))
    return markup

def companies_kb(page, total_pages):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if total_pages > 1:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data="noop"))
        
        nav_buttons.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data="noop"))
        
        markup.row(*nav_buttons)
    
    markup.row(
        types.InlineKeyboardButton("🏠 Главная", callback_data="main"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_companies")
    )
    return markup

# ========== КОМАНДА СТАРТ ==========

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user = message.from_user
    db_user = database.get_user(user.id, user.username, user.first_name)
    
    season = database.get_current_season()
    if season and season['active']:
        end = datetime.fromisoformat(str(season['end_date']))
        now = datetime.now()
        if now < end:
            delta = end - now
            time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
        else:
            time_left = ""
    else:
        time_left = ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${db_user['money']:,.2f}\n🏆 Кубков: {db_user['cubes']}{time_left}\n\n📆 День: {db_user['day']}"
    
    bot.send_photo(
        user.id,
        IMAGES['main'],
        caption=text,
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )

# ========== КОМАНДА ПОМОЩЬ ==========

@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = (
        "📚 *Помощь по игре*\n\n"
        "*Команды:*\n"
        "/start - начать игру\n"
        "/help - эта помощь\n"
        "/buy AAPL 5 - купить акции\n"
        "/sell AAPL 5 - продать акции\n"
        "/next - следующий день\n"
        "/stats - твоя статистика\n"
        "/list - список компаний\n"
        "/leader - таблица лидеров\n"
        "/send @user 1000 - перевести деньги\n"
        "/ref - реферальная ссылка\n\n"
        "*Магазин:*\n"
        "🚀 Ускоритель - 500$\n"
        "🛡️ Страховка - 300$\n"
        "📊 Аналитик - 200$\n"
        "🎲 Рандом - 100$\n"
        "💎 VIP (30 дн) - 5000$\n"
        "🎁 Лаки бокс - 300$"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=back_kb("main"))

# ========== КОМАНДА ПОКУПКИ ==========

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
        
        company = database.get_company(ticker)
        if not company:
            bot.reply_to(message, f"❌ Компания {ticker} не найдена")
            return
        
        user = database.get_user(user_id)
        total = company['price'] * amount
        
        if user['money'] < total:
            bot.reply_to(message, f"❌ Не хватает денег. Нужно ${total:,.2f}")
            return
        
        database.buy_stock(user_id, ticker, amount, company['price'])
        
        # Проверяем достижения
        new_achs = database.check_achievements(user_id)
        for ach in new_achs:
            info = database.ACHIEVEMENTS[ach]
            bot.send_message(
                user_id,
                f"🔔 *Новое достижение!*\n{info['emoji']} {info['name']}\n_{info['desc']}_",
                parse_mode="Markdown"
            )
        
        bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА ПРОДАЖИ ==========

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
        
        company = database.get_company(ticker)
        if not company:
            bot.reply_to(message, f"❌ Компания {ticker} не найдена")
            return
        
        portfolio = database.get_portfolio(user_id)
        stock = next((s for s in portfolio if s['ticker'] == ticker), None)
        
        if not stock or stock['amount'] < amount:
            bot.reply_to(message, f"❌ У тебя только {stock['amount'] if stock else 0} акций")
            return
        
        total = company['price'] * amount
        database.sell_stock(user_id, ticker, amount, company['price'])
        
        bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА СЛЕДУЮЩИЙ ДЕНЬ ==========

@bot.message_handler(commands=['next'])
def next_cmd(message):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    database.update_prices()
    database.update_day(user_id)
    
    bot.reply_to(message, f"⏩ День {user['day'] + 1}! Цены обновлены.")

# ========== КОМАНДА СПИСОК КОМПАНИЙ ==========

@bot.message_handler(commands=['list'])
def list_cmd(message):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    companies = database.get_all_companies()
    total_pages = (len(companies) + 9) // 10
    
    text = f"📋 *ВСЕ КОМПАНИИ (День {user['day']})*\n\n"
    
    for company in companies[:10]:
        change = utils.get_price_change(company['prev_price'], company['price'])
        emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
        text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
    
    bot.send_photo(
        user_id,
        IMAGES['companies'],
        caption=text,
        parse_mode="Markdown",
        reply_markup=companies_kb(1, total_pages)
    )

# ========== КОМАНДА СТАТИСТИКА ==========

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    portfolio = database.get_portfolio(user_id)
    
    total_capital = user['money']
    text = f"📊 *ТВОЯ СТАТИСТИКА (День {user['day']})*\n\n"
    text += f"💰 Баланс: ${user['money']:,.2f}\n"
    
    for stock in portfolio:
        total_capital += stock['amount'] * stock['price']
    
    text += f"💵 Капитал: ${total_capital:,.2f}\n"
    text += f"🏆 Кубков: {user['cubes']}\n"
    text += f"👥 Рефералов: {user['referrals']}\n\n"
    
    text += "📋 *Портфель:*\n"
    if portfolio:
        for p in portfolio:
            text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
    else:
        text += "Пусто\n"
    
    # Место в топе
    rank, total = database.get_user_rank(user_id)
    if rank:
        text += f"\n⭐ Место: {rank} из {total}"
    
    bot.send_photo(
        user_id,
        IMAGES['stats'],
        caption=text,
        parse_mode="Markdown",
        reply_markup=back_kb("main")
    )

# ========== КОМАНДА ЛИДЕРЫ ==========

@bot.message_handler(commands=['leader'])
def leader_cmd(message):
    user_id = message.from_user.id
    leaders = database.get_leaderboard(10)
    season = database.get_current_season()
    
    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*"
    if season and season['active']:
        text += f"\nСезон: {season['name']}"
    text += "\n\n"
    
    for i, user in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        name = user['username'] or user['first_name'] or f"User_{user['user_id']}"
        text += f"{medal} {name[:15]} — ${user['total']:,.2f} (🏆 {user['cubes']})\n"
    
    rank, total = database.get_user_rank(user_id)
    if rank:
        text += f"\nТвое место: {rank} из {total}"
    
    bot.send_photo(
        user_id,
        IMAGES['leaderboard'],
        caption=text,
        parse_mode="Markdown",
        reply_markup=back_kb("main")
    )

# ========== КОМАНДА ПЕРЕВОД ==========

@bot.message_handler(commands=['send'])
def send_cmd(message):
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /send @user 1000")
            return
        
        to_user = parts[1]
        amount = int(parts[2])
        
        success, msg = database.transfer_money(user_id, to_user, amount)
        bot.reply_to(message, msg)
        
        if success:
            # Проверяем достижения
            new_achs = database.check_achievements(user_id)
            for ach in new_achs:
                info = database.ACHIEVEMENTS[ach]
                bot.send_message(
                    user_id,
                    f"🔔 *Новое достижение!*\n{info['emoji']} {info['name']}\n_{info['desc']}_",
                    parse_mode="Markdown"
                )
                
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== АДМИН-КОМАНДЫ ==========

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ Доступ запрещен")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        text = (
            "👑 *АДМИН-КОМАНДЫ*\n\n"
            "/admin stats - статистика\n"
            "/admin give ID 5000 - выдать деньги\n"
            "/admin take ID 2000 - забрать деньги\n"
            "/admin cubes ID 3 - выдать кубки\n"
            "/admin reset ID - сбросить\n"
            "/admin mail ТЕКСТ - рассылка\n"
            "/admin season NAME DAYS - создать сезон"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
        return
    
    cmd = parts[1].lower()
    
    if cmd == "stats":
        stats = database.get_stats()
        text = (
            f"📊 *СТАТИСТИКА*\n\n"
            f"👥 Пользователей: {stats['users']}\n"
            f"📅 Активных: {stats['active']}\n"
            f"💰 Денег: ${stats['total_money']:,.2f}\n"
            f"📈 В акциях: ${stats['total_stocks']:,.2f}\n"
            f"💵 Капитал: ${stats['total_capital']:,.2f}\n"
            f"📊 Сделок: {stats['trades']}\n"
            f"👥 Рефералов: {stats['total_refs']}"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
    
    elif cmd == "give" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        database.update_money(target, amount)
        bot.reply_to(message, f"✅ Выдано ${amount} пользователю {target}")
    
    elif cmd == "take" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        database.update_money(target, -amount)
        bot.reply_to(message, f"✅ Забрано ${amount} у {target}")
    
    elif cmd == "cubes" and len(parts) >= 4:
        target = int(parts[2])
        amount = int(parts[3])
        database.update_cubes(target, amount)
        bot.reply_to(message, f"✅ Выдано {amount} кубков {target}")
    
    elif cmd == "reset" and len(parts) >= 3:
        target = int(parts[2])
        database.reset_user(target)
        bot.reply_to(message, f"✅ Пользователь {target} сброшен")
    
    elif cmd == "season" and len(parts) >= 4:
        name = parts[2]
        days = int(parts[3])
        database.create_season(name, days)
        bot.reply_to(message, f"✅ Сезон '{name}' на {days} дней создан")

# ========== ОБРАБОТКА КНОПОК ==========

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data
    
    try:
        if data == "main":
            user = database.get_user(uid)
            season = database.get_current_season()
            
            if season and season['active']:
                end = datetime.fromisoformat(str(season['end_date']))
                now = datetime.now()
                if now < end:
                    delta = end - now
                    time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
                else:
                    time_left = ""
            else:
                time_left = ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}{time_left}\n\n📆 День: {user['day']}"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_menu_kb()
            )
            bot.answer_callback_query(call.id)
        
        elif data == "stats":
            user = database.get_user(uid)
            portfolio = database.get_portfolio(uid)
            
            total_capital = user['money']
            text = f"📊 *ТВОЯ СТАТИСТИКА (День {user['day']})*\n\n"
            text += f"💰 Баланс: ${user['money']:,.2f}\n"
            
            for stock in portfolio:
                total_capital += stock['amount'] * stock['price']
            
            text += f"💵 Капитал: ${total_capital:,.2f}\n"
            text += f"🏆 Кубков: {user['cubes']}\n"
            text += f"👥 Рефералов: {user['referrals']}\n\n"
            
            text += "📋 *Портфель:*\n"
            if portfolio:
                for p in portfolio:
                    text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
            else:
                text += "Пусто\n"
            
            rank, total = database.get_user_rank(uid)
            if rank:
                text += f"\n⭐ Место: {rank} из {total}"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['stats'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_kb("main")
            )
            bot.answer_callback_query(call.id)
        
        elif data == "companies":
            user = database.get_user(uid)
            companies = database.get_all_companies()
            total_pages = (len(companies) + 9) // 10
            
            text = f"📋 *ВСЕ КОМПАНИИ (День {user['day']})*\n\n"
            
            for company in companies[:10]:
                change = utils.get_price_change(company['prev_price'], company['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['companies'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=companies_kb(1, total_pages)
            )
            bot.answer_callback_query(call.id)
        
        elif data.startswith("page_"):
            page = int(data.replace("page_", ""))
            user = database.get_user(uid)
            companies = database.get_all_companies()
            total_pages = (len(companies) + 9) // 10
            
            start = (page - 1) * 10
            end = start + 10
            page_companies = companies[start:end]
            
            text = f"📋 *ВСЕ КОМПАНИИ (День {user['day']})*\n\n"
            
            for company in page_companies:
                change = utils.get_price_change(company['prev_price'], company['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['companies'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=companies_kb(page, total_pages)
            )
            bot.answer_callback_query(call.id)
        
        elif data == "next":
            database.update_prices()
            database.update_day(uid)
            user = database.get_user(uid)
            
            bot.answer_callback_query(call.id, f"⏩ День {user['day']}!")
            
            # Обновляем главное меню
            season = database.get_current_season()
            if season and season['active']:
                end = datetime.fromisoformat(str(season['end_date']))
                now = datetime.now()
                if now < end:
                    delta = end - now
                    time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
                else:
                    time_left = ""
            else:
                time_left = ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}{time_left}\n\n📆 День: {user['day']}"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_menu_kb()
            )
        
        elif data == "leaderboard":
            leaders = database.get_leaderboard(10)
            season = database.get_current_season()
            
            text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*"
            if season and season['active']:
                text += f"\nСезон: {season['name']}"
            text += "\n\n"
            
            for i, user in enumerate(leaders, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                name = user['username'] or user['first_name'] or f"User_{user['user_id']}"
                text += f"{medal} {name[:15]} — ${user['total']:,.2f} (🏆 {user['cubes']})\n"
            
            rank, total = database.get_user_rank(uid)
            if rank:
                text += f"\nТвое место: {rank} из {total}"
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['leaderboard'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_kb("main")
            )
            bot.answer_callback_query(call.id)
        
        elif data == "help":
            text = (
                "📚 *Помощь по игре*\n\n"
                "*Команды:*\n"
                "/start - начать игру\n"
                "/help - эта помощь\n"
                "/buy AAPL 5 - купить акции\n"
                "/sell AAPL 5 - продать акции\n"
                "/next - следующий день\n"
                "/stats - твоя статистика\n"
                "/list - список компаний\n"
                "/leader - таблица лидеров\n"
                "/send @user 1000 - перевести деньги\n\n"
                "*Магазин:*\n"
                "🚀 Ускоритель - 500$\n"
                "🛡️ Страховка - 300$\n"
                "📊 Аналитик - 200$\n"
                "🎲 Рандом - 100$\n"
                "💎 VIP (30 дн) - 5000$\n"
                "🎁 Лаки бокс - 300$"
            )
            
            bot.edit_message_media(
                types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_kb("main")
            )
            bot.answer_callback_query(call.id)
        
        elif data == "noop":
            bot.answer_callback_query(call.id)
        
        else:
            bot.answer_callback_query(call.id, "⚙️ В разработке")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("🚀 Terminal Trade запущен с PostgreSQL!")
    print(f"👥 Админы: {ADMINS}")
    print(f"💰 Стартовый капитал: ${START_MONEY}")
    bot.infinity_polling()