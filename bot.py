import telebot
import random
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8740420404:AAHli4wJgrgiAKtXeAC7GreL-rtyc2OwMgo"
ADMIN_ID = 7040677455

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========== ДАННЫЕ ==========
start_date = "2024"
end_date = "2026"
total_users = 1247
total_games = 5842
total_bugs = "бесконечно"

memes = [
    "📉 График упал так же резко, как Terminal Trade...",
    "💀 Помнишь, как мы торговали? Я помню.",
    "⚰️ Terminal Trade не умер — он переродился",
    "🎲 Раньше ты торговал, теперь стреляешь. Прогресс?",
    "🔫 Ставки те же, просто теперь пуля вместо графика",
    "🐛 Багов было больше, чем кода",
    "💸 Последний трейд был фатальным",
]

# ========== КЛАВИАТУРЫ ==========
def main_menu(page=1):
    kb = InlineKeyboardMarkup(row_width=2)
    if page == 1:
        kb.add(
            InlineKeyboardButton("📜 История", callback_data="history"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("😢 Мемы", callback_data="meme"),
            InlineKeyboardButton("🪦 Могила", callback_data="grave"),
            InlineKeyboardButton("🔫 Возрождение", callback_data="rebirth"),
            InlineKeyboardButton("➡️ Далее", callback_data="menu_page_2")
        )
    elif page == 2:
        kb.add(
            InlineKeyboardButton("🔫 Русская рулетка", url="https://t.me/RussianRoulette_official_bot"),
            InlineKeyboardButton("📢 Канал студии", url="https://t.me/Catalyst_studios"),
            InlineKeyboardButton("⬅️ Назад", callback_data="menu_page_1")
        )
    if ADMIN_ID:
        kb.add(InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel"))
    return kb

def admin_menu_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📊 Статистика бота", callback_data="admin_stats"),
        InlineKeyboardButton("🎫 Создать промокод", callback_data="admin_create_promo"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    return kb

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.send_message(
        m.chat.id,
        f"🕯️ <b>TERMINAL TRADE</b> — ПЕРВЫЙ ПРОЕКТ\n\n"
        f"Привет, {m.from_user.first_name}.\n\n"
        f"Этот бот — дань уважения проекту, с которого всё начиналось.\n"
        f"Он не принимает ставки и не стреляет. Он просто помнит.\n\n"
        f"⬇️ Нажми на кнопки ниже, чтобы узнать историю.",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id

    # Навигация по меню
    if call.data == "menu_page_1":
        bot.edit_message_text("🕯️ <b>TERMINAL TRADE</b> — ПЕРВЫЙ ПРОЕКТ\n\nВыбери раздел:", cid, mid, reply_markup=main_menu(page=1))
        bot.answer_callback_query(call.id)
        return
    elif call.data == "menu_page_2":
        bot.edit_message_text("🔗 <b>ПОЛЕЗНЫЕ ССЫЛКИ</b>\n\nНаши актуальные проекты:", cid, mid, reply_markup=main_menu(page=2))
        bot.answer_callback_query(call.id)
        return
    elif call.data == "back_to_menu":
        bot.edit_message_text("🕯️ <b>TERMINAL TRADE</b> — ПЕРВЫЙ ПРОЕКТ\n\nВыбери раздел:", cid, mid, reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    # Основные разделы
    if call.data == "history":
        text = (
            "📜 <b>ИСТОРИЯ TERMINAL TRADE</b>\n\n"
            f"• Создан в {start_date} году\n"
            f"• Закрыт в {end_date} году\n"
            "• Первый проект Catalyst Studios\n"
            "• Торговля внутри Telegram\n"
            "• Собственная экономика и валюта\n\n"
            "<i>Причина закрытия: багов было больше, чем кода.</i>"
        )
        bot.edit_message_text(text, cid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_page_1")))
        bot.answer_callback_query(call.id)
        return

    if call.data == "stats":
        text = (
            "📊 <b>СТАТИСТИКА TERMINAL TRADE</b>\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"🎮 Сыграно игр: {total_games}\n"
            f"🐛 Поймано багов: {total_bugs}\n"
            f"💰 Всего ставок: потерян счёт\n\n"
            "<i>Цифры примерные. Точные данные утеряны вместе с сервером.</i>"
        )
        bot.edit_message_text(text, cid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_page_1")))
        bot.answer_callback_query(call.id)
        return

    if call.data == "meme":
        meme = random.choice(memes)
        text = f"😢 <b>ВОСПОМИНАНИЕ</b>\n\n{meme}"
        bot.edit_message_text(text, cid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_page_1")))
        bot.answer_callback_query(call.id)
        return

    if call.data == "grave":
        text = (
            "🪦 <b>ЗДЕСЬ ПОКОИТСЯ</b>\n\n"
            "TERMINAL TRADE\n"
            f"{start_date} — {end_date}\n\n"
            "Он не умер. Он переродился.\n\n"
            "<i>Зажги лампадку 👇</i>"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🕯️ Зажечь свечу", callback_data="light_candle"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="menu_page_1"))
        bot.edit_message_text(text, cid, mid, reply_markup=kb)
        bot.answer_callback_query(call.id)
        return

    if call.data == "light_candle":
        bot.answer_callback_query(call.id, "🕯️ Свеча зажжена. Terminal Trade помнят.", show_alert=True)
        return

    if call.data == "rebirth":
        text = (
            "🔫 <b>ВОЗРОЖДЕНИЕ</b>\n\n"
            "Terminal Trade не умер — он переродился в\n"
            "@RussianRoulette_official_bot\n\n"
            "Ставки те же, просто теперь пуля вместо графика.\n\n"
            "<i>Риск остался. Адреналин — тоже.</i>"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔫 Перейти в русскую рулетку", url="https://t.me/RussianRoulette_official_bot"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="menu_page_1"))
        bot.edit_message_text(text, cid, mid, reply_markup=kb)
        bot.answer_callback_query(call.id)
        return

    # ========== АДМИН-ПАНЕЛЬ ==========
    if call.data == "admin_panel":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
            return
        bot.edit_message_text("👑 <b>АДМИН ПАНЕЛЬ</b>\n\nВыбери действие:", cid, mid, reply_markup=admin_menu_kb())
        bot.answer_callback_query(call.id)
        return

    if call.data == "admin_stats":
        if uid != ADMIN_ID:
            return
        text = (
            "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
            f"🕯️ Terminal Trade Memorial Bot\n"
            f"📅 Создан: 13.04.2026\n"
            f"👥 Пользователей: (сбор данных...)\n"
            f"🎮 Команд обработано: (сбор данных...)"
        )
        bot.edit_message_text(text, cid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")))
        bot.answer_callback_query(call.id)
        return

    if call.data == "admin_create_promo":
        if uid != ADMIN_ID:
            return
        bot.send_message(uid, "Введите промокод и награду в формате:\nКОД ТИП КОЛИЧЕСТВО\nПример: TTLOVE gc 100")
        bot.register_next_step_handler_by_chat_id(uid, lambda m: create_promo_handler(m, cid, mid))
        bot.answer_callback_query(call.id)
        return

    if call.data == "admin_broadcast":
        if uid != ADMIN_ID:
            return
        bot.send_message(uid, "Введите текст рассылки:")
        bot.register_next_step_handler_by_chat_id(uid, lambda m: broadcast_handler(m, cid, mid))
        bot.answer_callback_query(call.id)
        return

# ========== ОБРАБОТЧИКИ АДМИНА ==========
def create_promo_handler(m, ocid, omid):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        code = parts[0].upper()
        reward_type = parts[1].lower()
        amount = int(parts[2])
        bot.send_message(m.chat.id, f"✅ Промокод {code} создан! (тип: {reward_type}, {amount})")
        # Здесь можно сохранять в БД, если нужно
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Формат: КОД ТИП КОЛИЧЕСТВО")
    bot.edit_message_reply_markup(ocid, omid, reply_markup=admin_menu_kb())

def broadcast_handler(m, ocid, omid):
    if m.from_user.id != ADMIN_ID:
        return
    text = m.text
    # Здесь нужна БД для рассылки, пока просто заглушка
    bot.send_message(m.chat.id, f"📢 Рассылка отправлена (в разработке)\n\nТекст: {text[:100]}")
    bot.edit_message_reply_markup(ocid, omid, reply_markup=admin_menu_kb())

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("✅ Terminal Trade Memorial Bot запущен!")
    print(f"👑 Admin ID: {ADMIN_ID}")
    bot.infinity_polling()