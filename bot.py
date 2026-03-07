import telebot
from telebot import types
import random
import time
from datetime import datetime

from config import TOKEN, ADMIN_ID, IMAGES, STORY, SHOP_ITEMS
import database
import utils

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TOKEN)

# Создаем базу данных при запуске
database.init_database()

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
                callback_data=f"inv_item_{item['id']}"
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
    username = message.from_user.username or message.from_user.first_name
    
    # Получаем или создаем пользователя
    user = database.get_user(uid, username)
    
    season = database.get_current_season()
    if season and season['active']:
        end = datetime.fromisoformat(season['end_date'])
        now = datetime.now()
        if now < end:
            delta = end - now
            time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
        else:
            time_left = ""
    else:
        time_left = ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
    
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
        amount = int(am)
        
        # Получаем компании
        companies = database.get_all_companies()
        company = next((c for c in companies if c['ticker'] == ticker), None)
        
        if not company:
            bot.reply_to(m, "❌ Нет такой компании")
            return
        
        # Получаем пользователя
        user = database.get_user(m.from_user.id)
        
        total = company['price'] * amount
        
        if user['money'] >= total:
            # Покупаем
            database.buy_stock(m.from_user.id, ticker, amount, company['price'])
            bot.reply_to(m, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        else:
            bot.reply_to(m, f"❌ Нужно ${total:,.2f}, у тебя ${user['money']:,.2f}")
            
    except Exception as e:
        bot.reply_to(m, "❌ Формат: /tbuy AAPL 5")

@bot.message_handler(commands=['tsell'])
def sell_stock_cmd(m):
    try:
        _, ticker, am = m.text.split()
        ticker = ticker.upper()
        amount = int(am)
        
        # Получаем компании
        companies = database.get_all_companies()
        company = next((c for c in companies if c['ticker'] == ticker), None)
        
        if not company:
            bot.reply_to(m, "❌ Нет такой компании")
            return
        
        # Получаем портфель
        portfolio = database.get_portfolio(m.from_user.id)
        stock = next((s for s in portfolio if s['ticker'] == ticker), None)
        
        if not stock or stock['amount'] < amount:
            bot.reply_to(m, f"❌ У тебя только {stock['amount'] if stock else 0} акций")
            return
        
        # Продаем
        total = company['price'] * amount
        database.sell_stock(m.from_user.id, ticker, amount, company['price'])
        bot.reply_to(m, f"✅ Продано {amount} {ticker} за ${total:,.2f}")
            
    except Exception as e:
        bot.reply_to(m, "❌ Формат: /tsell AAPL 5")

@bot.message_handler(commands=['tnext'])
def next_cmd(m):
    uid = m.from_user.id
    
    # Обновляем цены
    database.update_company_prices()
    
    # Увеличиваем день
    database.update_user_day(uid)
    
    # Получаем обновленного пользователя
    user = database.get_user(uid)
    
    season = database.get_current_season()
    if season and season['active']:
        end = datetime.fromisoformat(season['end_date'])
        now = datetime.now()
        if now < end:
            delta = end - now
            time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
        else:
            time_left = ""
    else:
        time_left = ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
    
    if IMAGES.get('main'):
        bot.send_photo(uid, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=['tpromo'])
def promo_activate_cmd(m):
    try:
        code = m.text.split()[1].upper()
        promo = database.get_promocode(code)
        
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
    user = database.get_user(uid)
    companies, total = database.get_companies_page(1)
    pages = (total + 9) // 10
    
    text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
    for company in companies:
        change = utils.get_price_change(company['prev_price'], company['price'])
        emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
        text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
    
    if IMAGES.get('companies'):
        bot.send_photo(uid, IMAGES['companies'], caption=text, reply_markup=companies_kb(1, pages))
    else:
        bot.send_message(uid, text, reply_markup=companies_kb(1, pages))

@bot.message_handler(commands=['tstats'])
def stats_cmd(m):
    uid = m.from_user.id
    user = database.get_user(uid)
    portfolio = database.get_portfolio(uid)
    
    # Считаем общий капитал
    total_money = user['money']
    text = f"📊 ТВОЯ СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n"
    
    for stock in portfolio:
        total_money += stock['price'] * stock['amount']
    
    text += f"💵 Капитал: ${total_money:,.2f}\n"
    text += f"🏆 Кубков: {user.get('cubes',0)}\n"
    
    if user.get('shields', 0) > 0:
        text += f"🛡️ Страховок: {user['shields']}\n"
    
    text += "\n📋 *Портфель:*\n"
    if portfolio:
        for p in portfolio:
            text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
    else:
        text += "Пусто\n"
    
    # Получаем место в топе
    leaderboard = database.get_leaderboard(50)
    for i, e in enumerate(leaderboard, 1):
        if e['user_id'] == uid:
            text += f"\n⭐ Место: {i} из {len(leaderboard)}"
            break
    
    if IMAGES.get('stats'):
        bot.send_photo(uid, IMAGES['stats'], caption=text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))
    else:
        bot.send_message(uid, text, parse_mode="Markdown", reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['tleader'])
def leader_cmd(m):
    leaderboard = database.get_leaderboard(10)
    text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
    
    for i, e in enumerate(leaderboard, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
    
    if IMAGES.get('leaderboard'):
        bot.send_photo(m.chat.id, IMAGES['leaderboard'], caption=text, reply_markup=back_kb("back_to_main"))
    else:
        bot.send_message(m.chat.id, text, reply_markup=back_kb("back_to_main"))

@bot.message_handler(commands=['inventory'])
def inventory_cmd(m):
    uid = m.from_user.id
    user = database.get_user(uid)
    inventory = database.get_inventory(uid)
    user['inventory'] = inventory
    
    text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
    if inventory:
        for i, item in enumerate(inventory, 1):
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
    promos = database.get_all_promocodes()
    text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
    for p in promos:
        rem = p['max_uses'] - p['used_count']
        text += f"`{p['code']}` — +${p['bonus']} (осталось {rem}/{p['max_uses']})\n"
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
    
    # Защита от чужих кнопок в группах
    if call.message.chat.type != 'private' and call.from_user.id != call.message.from_user.id:
        bot.answer_callback_query(call.id, "Это не твои кнопки 🤬", show_alert=True)
        return
    
    try:
        # ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ =====
        if data == "back_to_main":
            user = database.get_user(uid)
            
            season = database.get_current_season()
            if season and season['active']:
                end = datetime.fromisoformat(season['end_date'])
                now = datetime.now()
                if now < end:
                    delta = end - now
                    time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
                else:
                    time_left = ""
            else:
                time_left = ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
            
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

        # ===== СТАТУС =====
        if data == "status":
            user = database.get_user(uid)
            portfolio = database.get_portfolio(uid)
            
            # Считаем общий капитал
            total_money = user['money']
            text = f"📊 ТВОЯ СТАТИСТИКА (День {user['day']})\n\n💰 Баланс: ${user['money']:,.2f}\n"
            
            for stock in portfolio:
                total_money += stock['price'] * stock['amount']
            
            text += f"💵 Капитал: ${total_money:,.2f}\n"
            text += f"🏆 Кубков: {user.get('cubes',0)}\n"
            
            if user.get('shields', 0) > 0:
                text += f"🛡️ Страховок: {user['shields']}\n"
            
            text += "\n📋 *Портфель:*\n"
            if portfolio:
                for p in portfolio:
                    text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
            else:
                text += "Пусто\n"
            
            leaderboard = database.get_leaderboard(50)
            for i, e in enumerate(leaderboard, 1):
                if e['user_id'] == uid:
                    text += f"\n⭐ Место: {i} из {len(leaderboard)}"
                    break
            
            if IMAGES.get('stats'):
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
            user = database.get_user(uid)
            companies, total = database.get_companies_page(1)
            pages = (total + 9) // 10
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for company in companies:
                change = utils.get_price_change(company['prev_price'], company['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
            
            if IMAGES.get('companies'):
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
            # Обновляем цены
            database.update_company_prices()
            
            # Увеличиваем день
            database.update_user_day(uid)
            
            user = database.get_user(uid)
            
            season = database.get_current_season()
            if season and season['active']:
                end = datetime.fromisoformat(season['end_date'])
                now = datetime.now()
                if now < end:
                    delta = end - now
                    time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
                else:
                    time_left = ""
            else:
                time_left = ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
            
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

        # ===== ЛИДЕРЫ =====
        if data == "leaderboard":
            leaderboard = database.get_leaderboard(10)
            text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n\n"
            
            for i, e in enumerate(leaderboard, 1):
                medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
                text += f"{medal} {e['username'][:15]} — ${e['capital']:,.2f} (🏆 {e['cubes']})\n"
            
            if IMAGES.get('leaderboard'):
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
            
            if IMAGES.get('shop'):
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
            
            if IMAGES.get('shop'):
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
            
            user = database.get_user(uid)
            text = f"{item['emoji']} *{item['name']}*\n\n{item['description']}\n\n💰 Цена: ${item['price']}\n💳 Твой баланс: ${user['money']:,.2f}\n\nКупить?"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Купить", callback_data=f"buy_item_{item_id}"),
                types.InlineKeyboardButton("◀️ Назад", callback_data=f"shop_category_{item['category']}")
            )
            
            if IMAGES.get('shop'):
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
            item = SHOP_ITEMS.get(item_id)
            
            if not item:
                bot.answer_callback_query(call.id, "❌ Товар не найден")
                return
            
            user = database.get_user(uid)
            
            if user['money'] < item['price']:
                bot.answer_callback_query(call.id, f"❌ Нужно ${item['price']}", show_alert=True)
                return
            
            # Списываем деньги
            database.update_user_money(uid, -item['price'])
            
            # Добавляем в инвентарь
            database.add_to_inventory(uid, {
                'item_id': item_id,
                'name': item['name'],
                'emoji': item['emoji'],
                'description': item['description'],
                'category': item['category'],
                'effect': item.get('effect', 'none')
            })
            
            bot.answer_callback_query(call.id, f"✅ Куплен {item['emoji']} {item['name']}", show_alert=True)
            
            # Возвращаемся в категорию
            category = item['category']
            category_names = {
                'consumable': '📦 РАСХОДНИКИ',
                'subscription': '💎 ПОДПИСКИ',
                'special': '🎁 СПЕЦПРЕДЛОЖЕНИЯ'
            }
            
            text = f"{category_names.get(category, 'ТОВАРЫ')}\n\nВыбери товар:"
            
            if IMAGES.get('shop'):
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
            user = database.get_user(uid)
            inventory = database.get_inventory(uid)
            user['inventory'] = inventory
            
            text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
            if inventory:
                for i, item in enumerate(inventory, 1):
                    text += f"{i}. {item['emoji']} {item['name']}\n"
            else:
                text += "Пусто\n"
            text += f"\n🏆 Кубков: {user.get('cubes',0)}"
            
            if IMAGES.get('inventory'):
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
            item_id = int(data[9:])  # Это id из БД
            inventory = database.get_inventory(uid)
            
            item = next((i for i in inventory if i['id'] == item_id), None)
            
            if not item:
                bot.answer_callback_query(call.id, "❌ Предмет не найден")
                return
            
            text = f"{item['emoji']} *{item['name']}*\n\n{item.get('description', '')}\n\nАктивировать?"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Активировать", callback_data=f"use_item_{item['id']}"),
                types.InlineKeyboardButton("◀️ Назад", callback_data="inventory")
            )
            
            if IMAGES.get('inventory'):
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
            item_id = int(data[9:])
            inventory = database.get_inventory(uid)
            
            item = next((i for i in inventory if i['id'] == item_id), None)
            
            if not item:
                bot.answer_callback_query(call.id, "❌ Предмет не найден")
                return
            
            # Применяем эффект
            user = database.get_user(uid)
            effect_message = utils.activate_item_effect(user, item)
            
            # Удаляем предмет из инвентаря
            database.remove_from_inventory(uid, item_id)
            
            # Обновляем пользователя в БД если нужно
            if 'money' in user:
                database.update_user_money(uid, user['money'] - database.get_user(uid)['money'])
            
            bot.answer_callback_query(call.id, effect_message, show_alert=True)
            
            # Обновляем инвентарь
            user = database.get_user(uid)
            inventory = database.get_inventory(uid)
            user['inventory'] = inventory
            
            text = "🎒 ТВОЙ ИНВЕНТАРЬ\n\n"
            if inventory:
                for i, item in enumerate(inventory, 1):
                    text += f"{i}. {item['emoji']} {item['name']}\n"
            else:
                text += "Пусто\n"
            text += f"\n🏆 Кубков: {user.get('cubes',0)}"
            
            if IMAGES.get('inventory'):
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
            promos = database.get_all_promocodes()
            text = "🎟️ ДОСТУПНЫЕ ПРОМОКОДЫ\n\n"
            for p in promos:
                rem = p['max_uses'] - p['used_count']
                text += f"`{p['code']}` — +${p['bonus']} (осталось {rem}/{p['max_uses']})\n"
            text += "\nАктивировать: /tpromo КОД"
            
            if IMAGES.get('main'):
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
            
            if IMAGES.get('main'):
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
            user = database.get_user(uid)
            companies, total = database.get_companies_page(page)
            pages = (total + 9) // 10
            
            if page < 1 or page > pages:
                bot.answer_callback_query(call.id, "Нет страниц")
                return
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for company in companies:
                change = utils.get_price_change(company['prev_price'], company['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
            
            if IMAGES.get('companies'):
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
            user = database.get_user(uid)
            companies, total = database.get_companies_page(1)
            pages = (total + 9) // 10
            
            text = f"📋 ВСЕ КОМПАНИИ (День {user['day']})\n\n"
            for company in companies:
                change = utils.get_price_change(company['prev_price'], company['price'])
                emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
                text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
            
            if IMAGES.get('companies'):
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
            ok, msg = database.use_promo(uid, code)
            
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
            if ok:
                user = database.get_user(uid)
                
                season = database.get_current_season()
                if season and season['active']:
                    end = datetime.fromisoformat(season['end_date'])
                    now = datetime.now()
                    if now < end:
                        delta = end - now
                        time_left = f"\n📅 До конца сезона: {delta.days}д {delta.seconds//3600}ч"
                    else:
                        time_left = ""
                else:
                    time_left = ""
                
                text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user.get('cubes', 0)}{time_left}\n\n📆 День: {user['day']}"
                
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
    help_text = (
        "/admingive ID сумма - выдать деньги\n"
        "/admintake ID сумма - забрать деньги\n"
        "/adminreset ID - сбросить пользователя\n"
        "/adminpromo КОД БОНУС МАКС - создать промокод\n"
        "/adminpromodel КОД - удалить промокод\n"
        "/adminpromos - список промокодов\n"
        "/admincomps - список компаний\n"
        "/adminseason НАЗВАНИЕ ДНЕЙ - создать сезон\n"
        "/adminseasonend - завершить сезон\n"
        "/adminstats - статистика\n"
        "/admintop - топ игроков\n"
        "/addleader - обновить таблицу лидеров"
    )
    bot.reply_to(m, help_text)

@bot.message_handler(commands=['admingive'])
def admin_give(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, tid, am = m.text.split()
        tid = int(tid)
        am = float(am)
        database.update_user_money(tid, am)
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
        database.update_user_money(tid, -am)
        bot.reply_to(m, f"✅ Забрано ${am:,.2f}")
    except:
        bot.reply_to(m, "❌ /admintake ID СУММА")

@bot.message_handler(commands=['adminreset'])
def admin_reset(m):
    if m.from_user.id != ADMIN_ID:
        return
    # TODO: реализовать сброс пользователя
    bot.reply_to(m, "❌ Функция в разработке")

@bot.message_handler(commands=['adminpromo'])
def admin_promo_add(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, code, bonus, mu = m.text.split()
        if database.add_promocode(code, int(bonus), int(mu)):
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
        if database.delete_promocode(code):
            bot.reply_to(m, f"✅ Промокод {code} удалён")
        else:
            bot.reply_to(m, "❌ Не найден")
    except:
        bot.reply_to(m, "❌ /adminpromodel КОД")

@bot.message_handler(commands=['adminpromos'])
def admin_promos_list(m):
    if m.from_user.id != ADMIN_ID:
        return
    promos = database.get_all_promocodes()
    text = "🎟️ ПРОМОКОДЫ:\n"
    for p in promos:
        text += f"{p['code']} — ${p['bonus']} — {p['used_count']}/{p['max_uses']}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['admincomps'])
def admin_comps_list(m):
    if m.from_user.id != ADMIN_ID:
        return
    companies = database.get_all_companies()
    text = "📋 КОМПАНИИ:\n"
    for c in companies:
        text += f"{c['ticker']} — {c['name']} — ${c['price']:,.2f}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['adminseason'])
def admin_season_create(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, name, days = m.text.split()
        database.create_season(name, int(days))
        bot.reply_to(m, f"✅ Сезон '{name}' на {days} дней")
    except:
        bot.reply_to(m, "❌ /adminseason НАЗВАНИЕ ДНЕЙ")

@bot.message_handler(commands=['adminseasonend'])
def admin_season_end(m):
    if m.from_user.id != ADMIN_ID:
        return
    ok, msg = database.end_season()
    bot.reply_to(m, msg)

@bot.message_handler(commands=['adminstats'])
def admin_stats(m):
    if m.from_user.id != ADMIN_ID:
        return
    # TODO: реализовать статистику
    bot.reply_to(m, "❌ Функция в разработке")

@bot.message_handler(commands=['admintop'])
def admin_top(m):
    if m.from_user.id != ADMIN_ID:
        return
    top = database.get_leaderboard(10)
    text = "🏆 ТОП-10:\n"
    for i, e in enumerate(top, 1):
        text += f"{i}. {e['username']} — ${e['capital']:,.2f}\n"
    bot.reply_to(m, text)

@bot.message_handler(commands=['addleader'])
def admin_update_leaderboard(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        database.update_leaderboard()
        bot.reply_to(m, "✅ Таблица лидеров обновлена!")
    except Exception as e:
        bot.reply_to(m, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Terminal Trade запущен")
    print("✅ База данных SQLite")
    print("✅ Бот работает в чатах и ЛС")
    print("✅ Защита от чужих кнопок")
    print("✅ Сообщения редактируются")
    print("✅ Фото есть везде")
    bot.infinity_polling()