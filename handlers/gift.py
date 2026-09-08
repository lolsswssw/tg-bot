import random


GIFTS = [
    {"name": "🌹 Роза", "cost": 5, "emoji": "🌹"},
    {"name": "💎 Алмаз", "cost": 15, "emoji": "💎"},
    {"name": "🧸 Мишка", "cost": 10, "emoji": "🧸"},
    {"name": "🎂 Торт", "cost": 8, "emoji": "🎂"},
    {"name": "📱 Телефон", "cost": 50, "emoji": "📱"},
    {"name": "🎮 Игровая приставка", "cost": 100, "emoji": "🎮"},
    {"name": "✈️ Путешествие", "cost": 200, "emoji": "✈️"},
    {"name": "💰 Деньги", "cost": 30, "emoji": "💰"},
]

user_stars = {}


def get_stars(user_id):
    return user_stars.get(user_id, 100)


async def gift_command(event, client, args):
    user_id = event.sender_id
    stars = get_stars(user_id)

    gift_list = "\n".join([
        f"  {i+1}. {g['emoji']} {g['name']} — {g['cost']} ⭐"
        for i, g in enumerate(GIFTS)
    ])

    await event.reply(
        f"🎁 *Магазин подарков*\n\n"
        f"Ваш баланс: *{stars}* ⭐\n\n"
        f"Выберите подарок (номер):\n{gift_list}\n\n"
        f"Использование: `.gift <номер>`"
    )


async def gift_process(event, client, args):
    if not args or not args[0].isdigit():
        return False

    idx = int(args[0]) - 1
    if idx < 0 or idx >= len(GIFTS):
        await event.reply("❌ Неверный номер подарка.")
        return True

    gift = GIFTS[idx]
    user_id = event.sender_id
    stars = get_stars(user_id)

    if stars < gift["cost"]:
        await event.reply(f"❌ Недостаточно звёзд! Нужно {gift['cost']}, у вас {stars}.")
        return True

    user_stars[user_id] = stars - gift["cost"]
    new_balance = user_stars[user_id]

    await event.reply(
        f"🎁 *Подарок отправлен!*\n\n"
        f"Вы отправили {gift['emoji']} *{gift['name']}*\n\n"
        f"Списано: {gift['cost']} ⭐\n"
        f"Ваш баланс: {new_balance} ⭐"
    )
    return True
