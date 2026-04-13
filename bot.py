import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

# Твой токен
TOKEN = "8740420404:AAHli4wJgrgiAKtXeAC7GreL-rtyc2OwMgo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище игроков
players = {}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_player(user_id: int):
    if user_id not in players:
        players[user_id] = {
            "credits": 1000,
            "inventory": {"food": 0, "ore": 0, "tech": 0},
            "prices": {
                "food": random.randint(10, 30),
                "ore": random.randint(20, 50),
                "tech": random.randint(60, 120)
            }
        }
    return players[user_id]

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌍 Travel", callback_data="travel"),
        InlineKeyboardButton(text="📊 Market", callback_data="market")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Inventory", callback_data="inventory"),
        InlineKeyboardButton(text="🔄 Reset", callback_data="reset")
    )
    return builder.as_markup()

def market_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🍔 Buy Food", callback_data="buy_food"),
        InlineKeyboardButton(text="🍔 Sell Food", callback_data="sell_food")
    )
    builder.row(
        InlineKeyboardButton(text="⛏️ Buy Ore", callback_data="buy_ore"),
        InlineKeyboardButton(text="⛏️ Sell Ore", callback_data="sell_ore")
    )
    builder.row(
        InlineKeyboardButton(text="💻 Buy Tech", callback_data="buy_tech"),
        InlineKeyboardButton(text="💻 Sell Tech", callback_data="sell_tech")
    )
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="back"))
    return builder.as_markup()

def travel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Earth", callback_data="travel_earth"))
    builder.row(InlineKeyboardButton(text="🪐 Mars", callback_data="travel_mars"))
    builder.row(InlineKeyboardButton(text="🌌 Jupiter", callback_data="travel_jupiter"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="back"))
    return builder.as_markup()

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="back"))
    return builder.as_markup()

# ==================== КОМАНДА /start ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    text = f"🪐 *Terminal Trader*\n\n"
    text += f"📍 Location: *Earth*\n"
    text += f"💰 Balance: *{player['credits']} Cr*\n\n"
    text += f"🎯 Goal: earn 1,000,000 Cr"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# ==================== ОБРАБОТКА КНОПОК ====================

@dp.callback_query(F.data == "back")
async def back_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    
    text = f"🪐 *Terminal Trader*\n\n"
    text += f"📍 Location: *Earth*\n"
    text += f"💰 Balance: *{player['credits']} Cr*\n\n"
    text += f"🎯 Goal: earn 1,000,000 Cr"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "market")
async def market_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    
    # Обновляем цены при входе на рынок
    player["prices"] = {
        "food": random.randint(10, 30),
        "ore": random.randint(20, 50),
        "tech": random.randint(60, 120)
    }
    
    p = player["prices"]
    inv = player["inventory"]
    
    text = f"📊 *Market*\n\n"
    text += f"💰 Balance: {player['credits']} Cr\n\n"
    text += f"🍔 Food: Buy {p['food']} Cr | Sell {int(p['food']*0.7)} Cr (you have: {inv['food']})\n"
    text += f"⛏️ Ore: Buy {p['ore']} Cr | Sell {int(p['ore']*0.7)} Cr (you have: {inv['ore']})\n"
    text += f"💻 Tech: Buy {p['tech']} Cr | Sell {int(p['tech']*0.7)} Cr (you have: {inv['tech']})"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=market_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "inventory")
async def inventory_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    inv = player["inventory"]
    
    text = f"📦 *Inventory*\n\n"
    text += f"🍔 Food: {inv['food']}\n"
    text += f"⛏️ Ore: {inv['ore']}\n"
    text += f"💻 Tech: {inv['tech']}\n\n"
    text += f"💰 Balance: {player['credits']} Cr"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "travel")
async def travel_callback(callback: types.CallbackQuery):
    text = "🚀 *Select destination:*"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=travel_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("travel_"))
async def travel_to_callback(callback: types.CallbackQuery):
    planet = callback.data.replace("travel_", "").capitalize()
    await callback.answer(f"Travelled to {planet}!")
    await back_callback(callback)

@dp.callback_query(F.data == "reset")
async def reset_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    players[user_id] = {
        "credits": 1000,
        "inventory": {"food": 0, "ore": 0, "tech": 0},
        "prices": {}
    }
    await callback.answer("Game reset!")
    await back_callback(callback)

# ==================== ПОКУПКА ====================

@dp.callback_query(F.data == "buy_food")
async def buy_food(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = player["prices"]["food"]
    
    if player["credits"] >= price:
        player["credits"] -= price
        player["inventory"]["food"] += 1
        await callback.answer(f"Bought 1 food for {price} Cr")
    else:
        await callback.answer("Not enough credits!", show_alert=True)
    
    await market_callback(callback)

@dp.callback_query(F.data == "buy_ore")
async def buy_ore(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = player["prices"]["ore"]
    
    if player["credits"] >= price:
        player["credits"] -= price
        player["inventory"]["ore"] += 1
        await callback.answer(f"Bought 1 ore for {price} Cr")
    else:
        await callback.answer("Not enough credits!", show_alert=True)
    
    await market_callback(callback)

@dp.callback_query(F.data == "buy_tech")
async def buy_tech(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = player["prices"]["tech"]
    
    if player["credits"] >= price:
        player["credits"] -= price
        player["inventory"]["tech"] += 1
        await callback.answer(f"Bought 1 tech for {price} Cr")
    else:
        await callback.answer("Not enough credits!", show_alert=True)
    
    await market_callback(callback)

# ==================== ПРОДАЖА ====================

@dp.callback_query(F.data == "sell_food")
async def sell_food(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = int(player["prices"]["food"] * 0.7)
    
    if player["inventory"]["food"] > 0:
        player["credits"] += price
        player["inventory"]["food"] -= 1
        await callback.answer(f"Sold 1 food for {price} Cr")
    else:
        await callback.answer("No food to sell!", show_alert=True)
    
    await market_callback(callback)

@dp.callback_query(F.data == "sell_ore")
async def sell_ore(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = int(player["prices"]["ore"] * 0.7)
    
    if player["inventory"]["ore"] > 0:
        player["credits"] += price
        player["inventory"]["ore"] -= 1
        await callback.answer(f"Sold 1 ore for {price} Cr")
    else:
        await callback.answer("No ore to sell!", show_alert=True)
    
    await market_callback(callback)

@dp.callback_query(F.data == "sell_tech")
async def sell_tech(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id)
    price = int(player["prices"]["tech"] * 0.7)
    
    if player["inventory"]["tech"] > 0:
        player["credits"] += price
        player["inventory"]["tech"] -= 1
        await callback.answer(f"Sold 1 tech for {price} Cr")
    else:
        await callback.answer("No tech to sell!", show_alert=True)
    
    await market_callback(callback)

# ==================== ЗАПУСК ====================

async def main():
    print("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())