from datetime import datetime
import random

def get_price_change(old, new):
    """Получить изменение цены в процентах"""
    if old == 0:
        return "0.00%"
    return f"{((new - old) / old) * 100:+.2f}%"

def calculate_capital(user):
    """Посчитать общий капитал пользователя"""
    return user['money']  # В БД считаем по-другому

def activate_item_effect(user, item, db_cursor=None):
    """Применить эффект предмета"""
    effect_message = ""
    
    if item['effect'] == 'booster':
        # Ускоритель
        effect_message = "🚀 Ускоритель активирован! Цены будут расти на 50% быстрее в течение 24 часов."
        
    elif item['effect'] == 'shield':
        # Страховка
        user['shields'] = user.get('shields', 0) + 1
        effect_message = "🛡️ Страховка активирована! Вы защищены от одного убытка."
        
    elif item['effect'] == 'analyst':
        # Аналитик
        effect_message = "📊 Аналитик: прогноз на завтра (скоро будет)"
        
    elif item['effect'] == 'random':
        # Рандом
        bonus = random.randint(50, 500)
        user['money'] += bonus
        effect_message = f"🎲 Случайный бонус: +${bonus}!"
        
    elif item['effect'] in ['vip', 'trader', 'investor']:
        # Подписки
        effect_message = f"{item['emoji']} Подписка {item['name']} активирована!"
        
    elif item['effect'] == 'lucky_box':
        # Лаки бокс
        chance = random.random()
        if chance < 0.3:
            bonus = random.randint(100, 1000)
            user['money'] += bonus
            effect_message = f"🎁 Вам выпало: ${bonus}!"
        elif chance < 0.6:
            effect_message = f"🎁 Вам выпал предмет!"
        else:
            effect_message = "🎁 Вам ничего не выпало... Повезет в следующий раз!"
    
    return effect_message