import telebot
from telebot import types
import random
import time
from datetime import datetime, timedelta

from config import TOKEN, ADMINS, IMAGES, STORY, SHOP_ITEMS, VERSION
import database
import utils

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TOKEN)

# Создаем базу данных
database.init_all()

# Добавляем поля для рефералов (если их нет)
try:
    database.add_referral_fields()
except:
    pass

# Временное хранилище для рефералов
referral_temp = {}

# ========== КНОПКИ ГЛАВНОГО МЕНЮ ==========

def main_menu_kb(page=1):
    """Клавиатура главного меню с пагинацией"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # Страница 1
    if page == 1:
        markup.add(
            types.InlineKeyboardButton("📊 Статус", callback_data="status"),
            types.InlineKeyboardButton("📈 Компании", callback_data="list"),
            types.InlineKeyboardButton("⏩ Next", callback_data="next")
        )
        markup.add(
            types.InlineKeyboardButton("🏆 Лидеры", callback_data="leaderboard"),
            types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
            types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory")
        )
        markup.add(
            types.InlineKeyboardButton("🏆 Кубки", callback_data="cubes"),
            types.InlineKeyboardButton("🎟️ Промо", callback_data="promo"),
            types.InlineKeyboardButton("👥 Рефералы", callback_data="ref_system")
        )
        markup.add(
            types.InlineKeyboardButton("❓ Помощь", callback_data="help"),
            types.InlineKeyboardButton("▶️ 2/2", callback_data="menu_page_2")
        )
    
    # Страница 2 (админка)
    elif page == 2:
        markup.add(
            types.InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel")
        )
        markup.add(
            types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats_show"),
            types.InlineKeyboardButton("📨 Рассылка", callback_data="admin_mail_start"),
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
        )
        markup.add(
            types.InlineKeyboardButton("🎟️ Промокоды", callback_data="admin_promos_list"),
            types.InlineKeyboardButton("🏆 Сезоны", callback_data="admin_seasons_menu"),
            types.InlineKeyboardButton("📦 Предметы", callback_data="admin_items")
        )
        markup.add(
            types.InlineKeyboardButton("◀️ 1/2", callback_data="menu_page_1")
        )
    
    return markup

def back_kb(target):
    """Кнопка назад"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data=target))
    return markup

def back_to_main_kb():
    """Кнопка назад в главное меню"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_main"))
    return markup

# ========== КНОПКИ МАГАЗИНА ==========

def shop_kb():
    """Клавиатура магазина"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📦 РАСХОДНИКИ", callback_data="shop_category_consumable"),
        types.InlineKeyboardButton("💎 ПОДПИСКИ", callback_data="shop_category_subscription"),
        types.InlineKeyboardButton("🎁 СПЕЦПРЕДЛОЖЕНИЯ", callback_data="shop_category_special"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup

def shop_category_kb(category, page=1):
    """Клавиатура категории магазина"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    items = []
    for item_id, item in SHOP_ITEMS.items():
        if item['category'] == category:
            items.append((item_id, item))
    
    # Пагинация по 5 товаров
    per_page = 5
    total_pages = (len(items) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    for item_id, item in items[start:end]:
        markup.add(types.InlineKeyboardButton(
            f"{item['emoji']} {item['name']} — ${item['price']}",
            callback_data=f"shop_item_{item_id}"
        ))
    
    # Кнопки пагинации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"shop_category_{category}_page_{page-1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"shop_category_{category}_page_{page+1}"))
    
    if len(nav_buttons) > 1:
        markup.row(*nav_buttons)
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="shop"))
    return markup

# ========== КНОПКИ ИНВЕНТАРЯ ==========

def inventory_kb(user_id, page=1):
    """Клавиатура инвентаря с пагинацией"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    items, total = database.get_inventory(user_id, page, 8)
    total_pages = (total + 7) // 8
    
    for i, item in enumerate(items):
        markup.add(types.InlineKeyboardButton(
            f"{item['emoji']} {item['name']}",
            callback_data=f"inv_item_{item['id']}"
        ))
    
    # Кнопки пагинации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"inventory_page_{page-1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"inventory_page_{page+1}"))
    
    if len(nav_buttons) > 1:
        markup.row(*nav_buttons)
    
    # Кнопка кубков
    user = database.get_user(user_id)
    if user['cubes'] > 0:
        markup.add(types.InlineKeyboardButton(f"🏆 Кубки: {user['cubes']}", callback_data="cubes"))
    
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
    return markup

# ========== КНОПКИ КОМПАНИЙ ==========

def companies_kb(page, total_pages):
    """Клавиатура компаний с пагинацией"""
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
        types.InlineKeyboardButton("🏠 Главная", callback_data="back_to_main"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_companies")
    )
    return markup

# ========== КНОПКИ РЕФЕРАЛОВ ==========

def ref_kb():
    """Клавиатура реферальной системы"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔗 Моя ссылка", callback_data="ref_link"),
        types.InlineKeyboardButton("➕ Добавить друга", callback_data="ref_add"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="ref_stats"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup

# ========== КНОПКИ АДМИНКИ ==========

def admin_kb():
    """Клавиатура админ-панели"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💰 Выдать деньги", callback_data="admin_give_money"),
        types.InlineKeyboardButton("💸 Забрать деньги", callback_data="admin_take_money"),
        types.InlineKeyboardButton("🏆 Выдать кубки", callback_data="admin_give_cubes"),
        types.InlineKeyboardButton("📦 Выдать предмет", callback_data="admin_give_item"),
        types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="admin_user_info"),
        types.InlineKeyboardButton("🔄 Сброс юзера", callback_data="admin_reset_user"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats_show"),
        types.InlineKeyboardButton("📨 Рассылка", callback_data="admin_mail_start"),
        types.InlineKeyboardButton("🎟️ Промокоды", callback_data="admin_promos_list"),
        types.InlineKeyboardButton("🏆 Сезоны", callback_data="admin_seasons_menu"),
        types.InlineKeyboardButton("📜 Логи", callback_data="admin_logs_show"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup

# ========== КОМАНДА СТАРТ ==========

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """Обработка команды /start"""
    user = message.from_user
    text = message.text
    
    # Проверяем реферальный код
    if len(text.split()) > 1 and text.split()[1].startswith('ref_'):
        try:
            ref_id = int(text.split()[1].replace('ref_', ''))
            
            if ref_id != user.id:  # Не сам себя
                # Начисляем бонус пригласившему
                conn = database.get_db()
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE users SET money = money + 500, referrals = referrals + 1 WHERE user_id = ?",
                    (ref_id,)
                )
                
                # Начисляем бонус новому пользователю
                cursor.execute(
                    "UPDATE users SET money = money + 200 WHERE user_id = ?",
                    (user.id,)
                )
                
                conn.commit()
                conn.close()
                
                # Уведомляем пригласившего
                try:
                    bot.send_message(
                        ref_id,
                        f"🎉 По твоей ссылке зарегистрировался {user.first_name}!\n+500$"
                    )
                except:
                    pass
                
                bot.send_message(
                    user.id,
                    "🎉 Ты пришел по реферальной ссылке!\n+200$ бонус!"
                )
        except:
            pass
    
    db_user = database.get_user(user.id)
    
    # Обновляем username если есть
    if user.username:
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ?, first_name = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user.username, user.first_name, user.id)
        )
        conn.commit()
        conn.close()
    
    season = database.get_current_season()
    if season and season['active']:
        days, hours = database.get_season_time_left()
        time_left = f"\n📅 До конца сезона: {days}д {hours}ч" if days else ""
    else:
        time_left = ""
    
    text = f"{STORY}\n\n💰 Твой баланс: ${db_user['money']:,.2f}\n🏆 Кубков: {db_user['cubes']}{time_left}\n\n📆 День: {db_user['day']}"
    
    if user.id in ADMINS:
        if IMAGES.get('main'):
            bot.send_photo(user.id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb(1))
        else:
            bot.send_message(user.id, text, parse_mode="Markdown", reply_markup=main_menu_kb(1))
    else:
        if IMAGES.get('main'):
            bot.send_photo(user.id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb(1))
        else:
            bot.send_message(user.id, text, parse_mode="Markdown", reply_markup=main_menu_kb(1))

# ========== КОМАНДА ПОМОЩЬ ==========

@bot.message_handler(commands=['help'])
def help_cmd(message):
    """Обработка команды /help"""
    user = message.from_user
    database.get_user(user.id)
    
    text = (
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
        "/inventory - инвентарь\n"
        "/cubes - твои кубки\n"
        "/achievements - достижения\n"
        "/ref - реферальная система"
    )
    
    bot.send_message(user.id, text, parse_mode="Markdown", reply_markup=back_to_main_kb())

# ========== КОМАНДА РЕФЕРАЛЫ ==========

@bot.message_handler(commands=['ref'])
def ref_cmd(message):
    """Реферальная система"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    referrals = user.get('referrals', 0)
    bonus = user.get('referral_bonus', 0)
    
    text = (
        "👥 *РЕФЕРАЛЬНАЯ СИСТЕМА*\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        "🔗 **Твоя ссылка:**\n"
        f"`{ref_link}`\n\n"
        "🎁 **Бонусы:**\n"
        "• За друга: +500$\n"
        "• Другу: +200$\n"
        "• 5% от покупок друга\n\n"
        f"📊 **Твоя статистика:**\n"
        f"• Приглашено: {referrals} чел.\n"
        f"• Заработано: ${bonus}\n\n"
        "👉 Нажми кнопку чтобы добавить друга"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=ref_kb())

# ========== КОМАНДА ПОКУПКИ ==========

@bot.message_handler(commands=['tbuy'])
def buy_cmd(message):
    """Купить акции"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /tbuy AAPL 5")
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
            bot.reply_to(message, f"❌ Не хватает денег. Нужно ${total:,.2f}, у тебя ${user['money']:,.2f}")
            return
        
        database.buy_stock(user_id, ticker, amount, company['price'])
        
        # Проверяем достижения
        new_achievements = database.check_achievements(user_id)
        for ach in new_achievements:
            info = utils.get_achievement_info(ach)
            bot.send_message(
                user_id,
                f"🔔 *Новое достижение!*\n{info['emoji']} {info['name']}\n_{info['description']}_",
                parse_mode="Markdown"
            )
        
        bot.reply_to(message, f"✅ Куплено {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА ПРОДАЖИ ==========

@bot.message_handler(commands=['tsell'])
def sell_cmd(message):
    """Продать акции"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Используй: /tsell AAPL 5")
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
        
        # Проверяем достижения
        new_achievements = database.check_achievements(user_id)
        for ach in new_achievements:
            info = utils.get_achievement_info(ach)
            bot.send_message(
                user_id,
                f"🔔 *Новое достижение!*\n{info['emoji']} {info['name']}\n_{info['description']}_",
                parse_mode="Markdown"
            )
        
        bot.reply_to(message, f"✅ Продано {amount} {ticker} за ${total:,.2f}")
        
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА СЛЕДУЮЩИЙ ДЕНЬ ==========

@bot.message_handler(commands=['tnext'])
def next_cmd(message):
    """Следующий день"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    database.update_all_prices()
    database.update_user_day(user_id)
    
    # Проверяем истекшие эффекты
    database.remove_expired_effects()
    database.remove_expired_subscriptions()
    
    season = database.get_current_season()
    if season and season['active']:
        days, hours = database.get_season_time_left()
        time_left = f"\n📅 До конца сезона: {days}д {hours}ч" if days else ""
    else:
        time_left = ""
    
    text = f"⏩ *День {user['day'] + 1}*\n\n{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}{time_left}"
    
    if IMAGES.get('main'):
        bot.send_photo(user_id, IMAGES['main'], caption=text, parse_mode="Markdown", reply_markup=main_menu_kb(1))
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_menu_kb(1))

# ========== КОМАНДА СПИСОК КОМПАНИЙ ==========

@bot.message_handler(commands=['tlist'])
def list_cmd(message):
    """Список компаний"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    companies = database.get_all_companies()
    total_pages = (len(companies) + 9) // 10
    
    text = f"📋 *ВСЕ КОМПАНИИ (День {user['day']})*\n\n"
    
    for company in companies[:10]:
        change = utils.get_price_change(company['prev_price'], company['price'])
        emoji = "🟢" if change.startswith('+') else "🔴" if change.startswith('-') else "⚪"
        text += f"{company['ticker']} — {company['name']}\n💰 ${company['price']:,.2f} {emoji} {change}\n\n"
    
    if IMAGES.get('companies'):
        bot.send_photo(user_id, IMAGES['companies'], caption=text, parse_mode="Markdown", reply_markup=companies_kb(1, total_pages))
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=companies_kb(1, total_pages))

# ========== КОМАНДА СТАТИСТИКА ==========

@bot.message_handler(commands=['tstats'])
def stats_cmd(message):
    """Статистика игрока"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    portfolio = database.get_portfolio(user_id)
    transactions = database.get_user_transactions(user_id, 5)
    
    total_capital = user['money']
    text = f"📊 *ТВОЯ СТАТИСТИКА (День {user['day']})*\n\n"
    text += f"💰 Баланс: ${user['money']:,.2f}\n"
    
    for stock in portfolio:
        total_capital += stock['amount'] * stock['price']
    
    text += f"💵 Капитал: ${total_capital:,.2f}\n"
    text += f"🏆 Кубков: {user['cubes']}\n"
    
    if user['shields'] > 0:
        text += f"🛡️ Страховок: {user['shields']}\n"
    
    # Рефералы
    referrals = user.get('referrals', 0)
    if referrals > 0:
        text += f"👥 Рефералов: {referrals}\n"
    
    # Активные эффекты
    effects = database.get_active_effects(user_id)
    if effects:
        text += "\n✨ *Активные эффекты:*\n"
        for e in effects:
            text += f"• {e['effect_type']}\n"
    
    # Подписки
    subs = database.get_active_subscriptions(user_id)
    if subs:
        text += "\n💎 *Подписки:*\n"
        for s in subs:
            text += f"• +{s['bonus']}% до {s['expires_at'][:10]}\n"
    
    text += "\n📋 *Портфель:*\n"
    if portfolio:
        for p in portfolio:
            text += f"{p['ticker']}: {p['amount']} шт. (${p['amount']*p['price']:,.2f})\n"
    else:
        text += "Пусто\n"
    
    # Последние сделки
    if transactions:
        text += "\n📜 *Последние сделки:*\n"
        for t in transactions[:3]:
            emoji = "🟢" if t['type'] == 'buy' else "🔴"
            text += f"{emoji} {t['ticker']} {t['amount']} шт. ${t['total']:,.2f}\n"
    
    # Место в топе
    rank, total = database.get_user_rank(user_id)
    if rank:
        text += f"\n⭐ Место: {rank} из {total}"
    
    if IMAGES.get('stats'):
        bot.send_photo(user_id, IMAGES['stats'], caption=text, parse_mode="Markdown", reply_markup=back_to_main_kb())
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_to_main_kb())

# ========== КОМАНДА ЛИДЕРЫ ==========

@bot.message_handler(commands=['tleader'])
def leader_cmd(message):
    """Таблица лидеров"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    leaderboard = database.get_leaderboard(10)
    season = database.get_current_season()
    
    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*"
    if season and season['active']:
        text += f"\nСезон: {season['name']}"
    
    text += "\n\n"
    
    for i, user in enumerate(leaderboard, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {user['username'][:15]} — ${user['capital']:,.2f} (🏆 {user['cubes']})\n"
    
    rank, total = database.get_user_rank(user_id)
    if rank:
        text += f"\nТвое место: {rank} из {total}"
    
    if IMAGES.get('leaderboard'):
        bot.send_photo(user_id, IMAGES['leaderboard'], caption=text, parse_mode="Markdown", reply_markup=back_to_main_kb())
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_to_main_kb())

# ========== КОМАНДА ПРОМОКОДЫ ==========

@bot.message_handler(commands=['promo'])
def promo_list_cmd(message):
    """Список промокодов"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    promos = database.get_all_promocodes()
    
    text = "🎟️ *ДОСТУПНЫЕ ПРОМОКОДЫ*\n\n"
    for p in promos[:10]:
        remaining = p['max_uses'] - p['used_count']
        text += f"`{p['code']}` — +${p['bonus']} (осталось {remaining}/{p['max_uses']})\n"
    
    if not promos:
        text += "Пока нет активных промокодов\n"
    
    text += "\nАктивировать: /tpromo КОД"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_to_main_kb())

@bot.message_handler(commands=['tpromo'])
def promo_activate_cmd(message):
    """Активация промокода"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используй: /tpromo КОД")
            return
        
        code = parts[1].strip().upper()
        success, msg = database.use_promocode(user_id, code)
        
        bot.reply_to(message, msg)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== КОМАНДА МАГАЗИН ==========

@bot.message_handler(commands=['shop'])
def shop_cmd(message):
    """Магазин"""
    user_id = message.from_user.id
    database.get_user(user_id)
    
    text = "🛒 *МАГАЗИН*\n\nВыбери категорию:"
    
    if IMAGES.get('shop'):
        bot.send_photo(user_id, IMAGES['shop'], caption=text, parse_mode="Markdown", reply_markup=shop_kb())
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=shop_kb())

# ========== КОМАНДА ИНВЕНТАРЬ ==========

@bot.message_handler(commands=['inventory'])
def inventory_cmd(message):
    """Инвентарь"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    items, total = database.get_inventory(user_id, 1, 8)
    
    text = "🎒 *ТВОЙ ИНВЕНТАРЬ*\n\n"
    
    if items:
        text += "📦 *Предметы:*\n"
        for i, item in enumerate(items, 1):
            text += f"{i}. {item['emoji']} {item['name']}\n"
    else:
        text += "📦 Инвентарь пуст\n"
    
    text += f"\n🏆 Кубков: {user['cubes']}"
    
    if total > 8:
        text += f"\n📊 Всего предметов: {total}"
    
    if IMAGES.get('inventory'):
        bot.send_photo(user_id, IMAGES['inventory'], caption=text, parse_mode="Markdown", reply_markup=inventory_kb(user_id, 1))
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=inventory_kb(user_id, 1))

# ========== КОМАНДА КУБКИ ==========

@bot.message_handler(commands=['cubes'])
def cubes_cmd(message):
    """Кубки пользователя"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    history = database.get_cubes_history(user_id)
    
    text = f"🏆 *ТВОИ КУБКИ*\n\nВсего: {user['cubes']}\n"
    
    if history:
        text += "\n📜 *История:*\n"
        for h in history:
            place_emoji = "🥇" if h['place'] == 1 else "🥈" if h['place'] == 2 else "🥉"
            text += f"{place_emoji} {h['season_name']} — {h['place']} место\n"
    else:
        text += "\nУ тебя пока нет кубков"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_kb("inventory"))

# ========== КОМАНДА ДОСТИЖЕНИЯ ==========

@bot.message_handler(commands=['achievements'])
def achievements_cmd(message):
    """Достижения"""
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    achievements = database.get_user_achievements(user_id)
    
    text = "🎯 *ТВОИ ДОСТИЖЕНИЯ*\n\n"
    
    if achievements:
        for a in achievements:
            info = utils.get_achievement_info(a['achievement_id'])
            text += f"{info['emoji']} *{info['name']}*\n_{info['description']}_\n📅 {a['achieved_at'][:10]}\n\n"
    else:
        text += "Пока нет достижений. Играй и получай!"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=back_to_main_kb())

# ========== АДМИН-КОМАНДЫ ==========

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    """Админ-команды"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ Доступ запрещен")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        # Показываем админ-панель
        text = "👑 *АДМИН-ПАНЕЛЬ*\n\nВыбери действие:"
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=admin_kb())
        return
    
    cmd = parts[1].lower()
    
    # /admin give money ID 5000
    if cmd == "give" and len(parts) >= 5:
        what = parts[2].lower()
        target_id = int(parts[3])
        amount = int(parts[4])
        
        if what == "money":
            database.update_user_money(target_id, amount)
            database.log_admin_action(user_id, f"GIVE_MONEY", str(target_id), f"{amount}")
            bot.reply_to(message, f"✅ Выдано ${amount} пользователю {target_id}")
        
        elif what == "cubes":
            database.update_user_cubes(target_id, amount)
            database.log_admin_action(user_id, f"GIVE_CUBES", str(target_id), f"{amount}")
            bot.reply_to(message, f"✅ Выдано {amount} кубков пользователю {target_id}")
        
        elif what == "item" and len(parts) >= 5:
            item_id = parts[4]
            if item_id in SHOP_ITEMS:
                database.add_to_inventory(target_id, SHOP_ITEMS[item_id])
                database.log_admin_action(user_id, f"GIVE_ITEM", str(target_id), item_id)
                bot.reply_to(message, f"✅ Выдан предмет {item_id} пользователю {target_id}")
            else:
                bot.reply_to(message, f"❌ Предмет {item_id} не найден")
    
    # /admin take money ID 2000
    elif cmd == "take" and len(parts) >= 5:
        what = parts[2].lower()
        target_id = int(parts[3])
        amount = int(parts[4])
        
        if what == "money":
            database.update_user_money(target_id, -amount)
            database.log_admin_action(user_id, f"TAKE_MONEY", str(target_id), f"{amount}")
            bot.reply_to(message, f"✅ Забрано ${amount} у пользователя {target_id}")
        
        elif what == "cubes":
            database.update_user_cubes(target_id, -amount)
            database.log_admin_action(user_id, f"TAKE_CUBES", str(target_id), f"{amount}")
            bot.reply_to(message, f"✅ Забрано {amount} кубков у пользователя {target_id}")
    
    # /admin info ID
    elif cmd == "info" and len(parts) >= 3:
        target_id = int(parts[2])
        target = database.get_user_by_id(target_id)
        
        if target:
            portfolio = database.get_portfolio(target_id)
            total = target['money']
            for p in portfolio:
                total += p['amount'] * p['price']
            
            text = f"👤 *Информация о пользователе*\n"
            text += f"🆔 ID: `{target['user_id']}`\n"
            text += f"📛 Username: @{target['username'] if target['username'] else 'нет'}\n"
            text += f"👤 Имя: {target['first_name']}\n"
            text += f"💰 Деньги: ${target['money']:,.2f}\n"
            text += f"💵 Капитал: ${total:,.2f}\n"
            text += f"🏆 Кубки: {target['cubes']}\n"
            text += f"👥 Рефералов: {target.get('referrals', 0)}\n"
            text += f"📆 День: {target['day']}\n"
            text += f"📅 Заходил: {target['last_seen'][:19]}"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Пользователь {target_id} не найден")
    
    # /admin reset ID
    elif cmd == "reset" and len(parts) >= 3:
        target_id = int(parts[2])
        
        # Сброс пользователя
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio WHERE user_id = ?", (target_id,))
        cursor.execute("DELETE FROM inventory WHERE user_id = ?", (target_id,))
        cursor.execute("DELETE FROM active_effects WHERE user_id = ?", (target_id,))
        cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (target_id,))
        cursor.execute("""
            UPDATE users 
            SET money = 1000.0, day = 1, cubes = 0, shields = 0 
            WHERE user_id = ?
        """, (target_id,))
        conn.commit()
        conn.close()
        
        database.log_admin_action(user_id, "RESET_USER", str(target_id))
        bot.reply_to(message, f"✅ Пользователь {target_id} сброшен")
    
    # /admin mail ТЕКСТ
    elif cmd == "mail" and len(parts) >= 3:
        text = " ".join(parts[2:])
        
        users = database.get_all_users(1000)
        sent = 0
        
        status_msg = bot.reply_to(message, f"📨 Начинаю рассылку {len(users)} пользователям...")
        
        for i, u in enumerate(users):
            try:
                bot.send_message(u['user_id'], f"📨 *РАССЫЛКА*\n\n{text}", parse_mode="Markdown")
                sent += 1
            except:
                pass
            
            if i % 10 == 0:
                try:
                    bot.edit_message_text(
                        f"📨 Рассылка... {i}/{len(users)}",
                        message.chat.id,
                        status_msg.message_id
                    )
                except:
                    pass
        
        database.log_admin_action(user_id, "MAIL", "", f"Sent to {sent}/{len(users)}")
        try:
            bot.edit_message_text(
                f"✅ Рассылка завершена!\nОтправлено: {sent}/{len(users)}",
                message.chat.id,
                status_msg.message_id,
                reply_markup=back_to_main_kb()
            )
        except:
            bot.reply_to(message, f"✅ Рассылка завершена! Отправлено: {sent}/{len(users)}", reply_markup=back_to_main_kb())

# ========== АДМИН-КОМАНДЫ (ОТДЕЛЬНЫЕ) ==========

@bot.message_handler(commands=['adminreset'])
def admin_reset(message):
    """Полный сброс пользователя"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ У вас нет прав администратора!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используйте: /adminreset ID")
            return
        
        target_id = int(parts[1])
        
        user = database.get_user_by_id(target_id)
        if not user:
            bot.reply_to(message, f"❌ Пользователь с ID {target_id} не найден")
            return
        
        conn = database.get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM portfolio WHERE user_id = ?", (target_id,))
        port_count = cursor.rowcount
        
        cursor.execute("DELETE FROM inventory WHERE user_id = ?", (target_id,))
        inv_count = cursor.rowcount
        
        cursor.execute("""
            UPDATE users 
            SET money = 1000.0, cubes = 0, day = 1, shields = 0 
            WHERE user_id = ?
        """, (target_id,))
        
        conn.commit()
        conn.close()
        
        database.log_admin_action(user_id, "RESET_USER", str(target_id), f"Портфель:{port_count}, Инвентарь:{inv_count}")
        
        bot.reply_to(
            message, 
            f"✅ Пользователь {target_id} сброшен!\n"
            f"💰 Баланс: 1000$\n"
            f"📦 Портфель: очищен ({port_count} позиций)\n"
            f"🎒 Инвентарь: очищен ({inv_count} предметов)\n"
            f"🏆 Кубки: 0\n"
            f"📆 День: 1"
        )
        
    except ValueError:
        bot.reply_to(message, "❌ ID должен быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    """Общая статистика бота"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ У вас нет прав администратора!")
        return
    
    try:
        conn = database.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE date(last_seen) = date('now')
        """)
        active_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(money) FROM users")
        total_money = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(p.amount * c.price) 
            FROM portfolio p
            JOIN companies c ON p.ticker = c.ticker
        """)
        total_portfolio = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(referrals) FROM users")
        total_refs = cursor.fetchone()[0] or 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_trades = cursor.fetchone()[0]
        except:
            total_trades = 0
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        companies_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inventory")
        items_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM promocodes")
        promos_count = cursor.fetchone()[0]
        
        conn.close()
        
        text = (
            f"📊 *СТАТИСТИКА БОТА*\n\n"
            f"👥 **Пользователи:** {users_count}\n"
            f"📅 **Активных сегодня:** {active_today}\n"
            f"💰 **Денег у игроков:** ${total_money:,.2f}\n"
            f"📈 **Стоимость портфелей:** ${total_portfolio:,.2f}\n"
            f"💵 **Общий капитал:** ${total_money + total_portfolio:,.2f}\n"
            f"👥 **Всего рефералов:** {total_refs}\n\n"
            f"🏢 **Компаний:** {companies_count}\n"
            f"📦 **Предметов в игре:** {items_count}\n"
            f"🎟️ **Промокодов:** {promos_count}\n"
            f"📊 **Всего сделок:** {total_trades}\n\n"
            f"🤖 *Версия бота: {VERSION}*"
        )
        
        database.log_admin_action(user_id, "STATS", "", f"Users:{users_count}")
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при получении статистики: {e}")

# ========== ОБРАБОТКА КНОПОК ==========

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработка нажатий на кнопки"""
    user_id = call.from_user.id
    data = call.data
    
    # Защита от чужих кнопок
    if call.message.chat.type != 'private':
        bot.answer_callback_query(call.id, "Это не твои кнопки 🤬", show_alert=True)
        return
    
    try:
        # ===== НАВИГАЦИЯ =====
        if data == "back_to_main":
            user = database.get_user(user_id)
            
            season = database.get_current_season()
            if season and season['active']:
                days, hours = database.get_season_time_left()
                time_left = f"\n📅 До конца сезона: {days}д {hours}ч" if days else ""
            else:
                time_left = ""
            
            text = f"{STORY}\n\n💰 Твой баланс: ${user['money']:,.2f}\n🏆 Кубков: {user['cubes']}{time_left}\n\n📆 День: {user['day']}"
            
            if IMAGES.get('main'):
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=main_menu_kb(1)
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_menu_kb(1)
                )
            bot.answer_callback_query(call.id)
            return
        
        # ===== ПАГИНАЦИЯ ГЛАВНОГО МЕНЮ =====
        if data.startswith("menu_page_"):
            page = int(data.replace("menu_page_", ""))
            
            if call.message.photo:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=main_menu_kb(page)
                )
            else:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=main_menu_kb(page)
                )
            bot.answer_callback_query(call.id)
            return
        
        # ===== РЕФЕРАЛЬНАЯ СИСТЕМА =====
        if data == "ref_system":
            user = database.get_user(user_id)
            
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            
            referrals = user.get('referrals', 0)
            bonus = user.get('referral_bonus', 0)
            
            text = (
                "👥 *РЕФЕРАЛЬНАЯ СИСТЕМА*\n\n"
                "Приглашай друзей и получай бонусы!\n\n"
                "🔗 **Твоя ссылка:**\n"
                f"`{ref_link}`\n\n"
                "🎁 **Бонусы:**\n"
                "• За друга: +500$\n"
                "• Другу: +200$\n"
                "• 5% от покупок друга\n\n"
                f"📊 **Твоя статистика:**\n"
                f"• Приглашено: {referrals} чел.\n"
                f"• Заработано: ${bonus}\n\n"
                "👉 Выбери действие:"
            )
            
            if call.message.photo:
                bot.edit_message_media(
                    types.InputMediaPhoto(IMAGES['main'], caption=text, parse_mode="Markdown"),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=ref_kb()
                )
            else:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=ref_kb()
                )
            bot.answer_callback_query(call.id)
            return
        
        if data == "ref_link":
            user = database.get_user(user_id)
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            
            text = (
                "🔗 *ТВОЯ РЕФЕРАЛЬНАЯ ССЫЛКА*\n\n"
                f"`{ref_link}`\n\n"
                "📋 Отправь эту ссылку друзьям!\n"
                "За каждого перешедшего получишь 500$"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=back_kb("ref_system")
            )
            bot.answer_callback_query(call.id)
            return
        
        if data == "ref_add":
            referral_temp[user_id] = True
            text = (
                "➕ *ДОБАВИТЬ ДРУГА*\n\n"
                "Отправь мне @username друга, который уже играет:\n"
                "Например: @durov\n\n"
                "Он получит 200$, ты 500$"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=back_kb("ref_system")
            )
            bot.answer_callback_query(call.id)
            return
        
        if data == "ref_stats":
            user = database.get_user(user_id)
            referrals = user.get('referrals', 0)
            bonus = user.get('referral_bonus', 0)
            
            # Получаем список рефералов (если есть)
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, first_name, money 
                FROM users 
                WHERE referred_by = ? 
                LIMIT 10
            """, (user_id,))
            ref_list = cursor.fetchall()
            conn.close()
            
            text = f"📊 *СТАТИСТИКА РЕФЕРАЛОВ*\n\n"
            text += f"👥 Приглашено: {referrals}\n"
            text += f"💰 Заработано: ${bonus}\n\n"
            
            if ref_list:
                text += "📋 *Последние рефералы:*\n"
                for r in ref_list:
                    name = r['first_name'] or r['username'] or "Неизвестно"
                    text += f"• {name}\n"
            else:
                text += "У тебя пока нет рефералов"
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=back_kb("ref_system")
            )
            bot.answer_callback_query(call.id)
            return
        
        # ... (остальные обработчики кнопок - статус, компании, next, лидеры, магазин и т.д.)
        # Они уже есть в твоем коде, я не буду их дублировать чтобы не засорять ответ
        
        # ===== ПУСТАЯ КНОПКА =====
        if data == "noop":
            bot.answer_callback_query(call.id)
            return
        
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")

# ========== ОБРАБОТКА ТЕКСТА ==========

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Обработка добавления друга по @username
    if user_id in referral_temp and text.startswith('@'):
        username = text[1:].lower()
        
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Ищем друга по username
        cursor.execute("SELECT user_id, first_name FROM users WHERE username = ?", (username,))
        friend = cursor.fetchone()
        
        if friend and friend['user_id'] != user_id:
            # Проверяем, не был ли уже добавлен
            cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (friend['user_id'],))
            referred = cursor.fetchone()
            
            if referred and referred['referred_by']:
                bot.reply_to(message, f"❌ @{username} уже чей-то реферал")
            else:
                # Начисляем бонусы
                cursor.execute("UPDATE users SET money = money + 500, referrals = referrals + 1 WHERE user_id = ?", (user_id,))
                cursor.execute("UPDATE users SET money = money + 200, referred_by = ? WHERE user_id = ?", (user_id, friend['user_id']))
                
                # Обновляем referral_bonus
                cursor.execute("UPDATE users SET referral_bonus = referral_bonus + 500 WHERE user_id = ?", (user_id,))
                
                conn.commit()
                
                bot.reply_to(
                    message, 
                    f"✅ @{username} добавлен как друг!\n"
                    f"Ты получил 500$, друг получил 200$"
                )
                
                # Уведомляем друга
                try:
                    bot.send_message(
                        friend['user_id'],
                        f"🎉 Пользователь @{message.from_user.username or 'кто-то'} добавил тебя как друга!\n+200$ бонус!"
                    )
                except:
                    pass
        else:
            bot.reply_to(message, f"❌ Пользователь @{username} не найден или это ты сам")
        
        conn.close()
        del referral_temp[user_id]
        return
    
    # Проверяем, есть ли состояние рассылки
    import os
    if os.path.exists(f"mail_state_{user_id}.txt") and user_id in ADMINS:
        if message.text == "/cancel":
            os.remove(f"mail_state_{user_id}.txt")
            bot.reply_to(message, "❌ Рассылка отменена", reply_markup=back_to_main_kb())
            return
        
        mail_text = message.text
        users = database.get_all_users(1000)
        
        status_msg = bot.reply_to(message, f"📨 Начинаю рассылку {len(users)} пользователям...")
        
        sent = 0
        for i, u in enumerate(users):
            try:
                bot.send_message(u['user_id'], mail_text, parse_mode="Markdown")
                sent += 1
            except:
                pass
            
            if i % 10 == 0:
                try:
                    bot.edit_message_text(
                        f"📨 Рассылка... {i}/{len(users)}",
                        message.chat.id,
                        status_msg.message_id
                    )
                except:
                    pass
        
        database.log_admin_action(user_id, "MAIL", "", f"Sent to {sent}/{len(users)}")
        
        try:
            bot.edit_message_text(
                f"✅ Рассылка завершена!\nОтправлено: {sent}/{len(users)}",
                message.chat.id,
                status_msg.message_id,
                reply_markup=back_to_main_kb()
            )
        except:
            bot.reply_to(message, f"✅ Рассылка завершена! Отправлено: {sent}/{len(users)}", reply_markup=back_to_main_kb())
        
        os.remove(f"mail_state_{user_id}.txt")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("🚀 Terminal Trade Bot запускается...")
    print(f"👤 Админы: {ADMINS}")
    print(f"📊 Версия: {VERSION}")
    print("✅ Бот готов к работе!")
    
    # Удаляем старые файлы состояний
    import os
    import glob
    for f in glob.glob("mail_state_*.txt"):
        try:
            os.remove(f)
        except:
            pass
    
    bot.infinity_polling()