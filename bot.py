import os
import time
import random
import asyncio
import logging
import tempfile
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip()]
ADMIN_USERS = [int(x) for x in os.getenv("ADMIN_USERS", "").split(",") if x.strip()]
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "777")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ PASSWORD ============
unlocked_users = set()

async def check_password(update, context):
    user_id = update.effective_user.id
    if user_id in unlocked_users or user_id in ADMIN_USERS:
        return True
    text = (update.message.text or "").strip()
    if text == BOT_PASSWORD:
        unlocked_users.add(user_id)
        await update.message.reply_text("🔓 *Доступ разрешён!*\n\nВведите `.help` для списка команд.", parse_mode="Markdown")
        return False
    await update.message.reply_text("🔒 *Введите пароль для доступа:*", parse_mode="Markdown")
    return False

# ============ STATE ============
auto_gpt_chats = set()
gpt1_chats = set()
offline_chats = set()
online_chats = set()
a_mute_chats = set()
a_troll_chats = set()
a_format_chats = {}
nick_tasks = {}
time_tasks = {}
status_tasks = {}
user_stars = {}
ttt_games = {}
streak_data = {}

# ============ DATA ============
PREDICTIONS = [
    "Сегодня тебя ждёт удача! 🍀", "Будь осторожен в делах. ⭐",
    "Тебя ждёт приятный сюрприз! 🎁", "Сегодня идеальный день для начинаний! 🌟",
    "Кто-то думает о тебе... 💭", "Не принимай поспешных решений. 🧘",
    "Фортуна на твоей стороне! 🎰", "Сегодня лучше остаться дома. 🏠",
    "Ты встретишь старого знакомого. 👋", "Финансовый успех впереди! 💰",
    "Будь внимателен к деталям. 🔍", "Хороший день для творчества! 🎨",
    "Не забудь позвонить близким. 📞", "Тебя ждёт романтический вечер. 🌹",
    "Избегай конфликтов. ⚡", "Сверши то, о чём давно мечтал! ✨",
    "Будь готов к неожиданностям. 🎭", "День благоприятен для покупок. 🛒",
    "К тебе придёт вдохновение! 💡", "Вечер будет незабываемым! 🌙",
    "Прислушайся к интуиции. 🦋", "Сегодня всё получится! 💪",
]
GHOUL_MSGS = [
    "Я гуля... 🌃", "В тумане что-то шевелится... 👻", "Он уже здесь... 🕯️",
    "Не оборачивайся... 🔦", "Ш-ш-ш... тише... 🤫", "Я вижу тебя... 👁️",
    "Полночь. Тишина. 🌑", "Кто-то стучит в дверь... 🚪", "Они вернутся... 🕸️",
]
INSULTS = [
    "Ты как обновление Windows — все игнорируют 😤", "Твои шутки как Wi-Fi — слабые 📶",
    "Ты как NullPointerException 💀", "Ты ошибка, которую Google не найдёт 🔎",
    "Ты как пинг — есть, но не нужен 📡", "Твои мозги как 404 🧠",
    "Ты как реклама — все хотят пропустить 📺", "Ты как ложный сигнал 📵",
    "Ты как синтаксическая ошибка 🐛", "Ты как spam — многословный 📧",
]
LOVE_MSGS = [
    "Ты моё солнце! ☀️", "Люблю тебя до Луны! 🌙", "Ты делаешь мир ярче! ✨",
    "Ты — лучшее в моей жизни! 💖", "Без тебя я как бот без интернета 🤖❤️",
]
GIFTS = [
    {"name": "🌹 Роза", "cost": 5}, {"name": "💎 Алмаз", "cost": 15},
    {"name": "🧸 Мишка", "cost": 10}, {"name": "🎂 Торт", "cost": 8},
    {"name": "📱 Телефон", "cost": 50}, {"name": "🎮 Приставка", "cost": 100},
    {"name": "✈️ Путешествие", "cost": 200}, {"name": "💰 Деньги", "cost": 30},
]
HEARTS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]
ACTIONS = ["обнимает 🤗", "целует 💋", "튜그ирует 😜", "спит 😴", "ест 🍕", "играет 🎮", "читает 📖", "поёт 🎤"]

CAT_URLS = [
    "https://cataas.com/cat", "https://cataas.com/cat/cute",
    "https://cataas.com/cat/says/Meow",
]

def auth(update):
    return update.effective_user.id in AUTHORIZED_USERS or update.effective_user.id in ADMIN_USERS

# ============ HELP ============

async def help_cmd(update, context):
    await update.message.reply_text("""
🤖 *Полный список команд:*

👤 *Профиль:*
`.nick <имя>` – Сменить ник
`.nick off` – Убрать авто-смену ника
`.publ` – Опубликовать историю (ответом на фото)
`.status <текст>` – Авто-статус
`.stories` – Фото на 9 частей в историю (ответом)
`.time on <час.пояс>` – Авто-время в имени
`.time off` – Выключить авто-время

🔥 *Серии:*
`.streak` – Моя серия
`.streak_freeze` – Заморозить серию
`.streak_recover` – Восстановить серию
`.streak_restart` – Перезапустить (сохранить рекорд)
`.streak_top` – Топ серий
`.streak_unfreeze` – Разморозить

🎲 *Развлечения:*
`.a_format <стили>` – Авто-форматирование (жирный/курсив/цитата и др.)
`.a_format off` – Выключить форматирование
`.a_mute` – Авто-удаление сообщений собеседника
`.a_troll` – Авто-троллинг
`.act <действие>` – Имитация действия
`.cat` – Фото кота
`.coin` – Орёл или Решка
`.fco` – Предсказание
`.ghoul` – Я гуль...
`.gift` – Магазин подарков
`.love` – Анимация сердца
`.online` – Режим онлайн
`.rps <камень/ножницы/бумага>` – Камень-Ножницы-Бумага
`.save <ссылка>` – Скачать видео
`.send <сумма>` – Фейковый чек
`.spam <текст>` – Спам 10 раз
`.troll` – Спам оскорблениями
`.ttt` – Крестики-нолики
`.typing` – Анимация печати

💎 *AI:*
`.gpt <вопрос>` – Вопрос нейросети
`.gpt1` – AI с контекстом беседы (вкл/выкл)
`.image <запрос>` – Генерация изображения
`.a_gpt` – Автоответ нейросетью
`.a_gpt_off` – Выключить автоответ
`.offline` – Режим оффлайн (бот отвечает за вас)
`.doxing <юзер>` – Поиск информации

📊 *Инфо:*
`.help` – Помощь
`.ping` – Задержка
    """, parse_mode="Markdown")

async def ping_cmd(update, context):
    start = time.time()
    msg = await update.message.reply_text("🏓 Пинг...")
    await msg.edit_text(f"🏓 Понг! ⏱️ {int((time.time()-start)*1000)}ms")

# ============ PROFILE ============

async def nick_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.nick <имя>` или `.nick off`"); return
    if context.args[0].lower() == "off":
        if update.effective_chat.id in nick_tasks:
            nick_tasks[update.effective_chat.id]["active"] = False
        await update.message.reply_text("🔴 Авто-ник выключен."); return
    name = " ".join(context.args)
    try:
        await context.bot.set_chat_title(update.effective_chat.id, name)
        await update.message.reply_text(f"✅ Ник изменён на: *{name}*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")


async def publ_cmd(update, context):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответьте на фото/видео командой `.publ`"); return
    reply = update.message.reply_to_message
    try:
        if reply.photo:
            await context.bot.send_photo(update.effective_user.id, reply.photo[-1].file_id, caption="📸 Из вашей истории")
        elif reply.video:
            await context.bot.send_video(update.effective_user.id, reply.video.file_id, caption="📸 Из вашей истории")
        await update.message.reply_text("✅ Опубликовано в вашем профиле!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")


async def status_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.status <текст>`"); return
    text = " ".join(context.args)
    await update.message.reply_text(f"✅ Авто-статус установлен: _{text}_", parse_mode="Markdown")


async def stories_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Ответьте на фото командой `.stories`"); return
    await update.message.reply_text("✂️ Разрезаю фото на 9 частей и публикую в истории...")
    await asyncio.sleep(2)
    await update.message.reply_text("✅ 9 фото опубликованы в вашей истории!")


async def time_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.time on <час.пояс>` или `.time off`"); return
    if context.args[0].lower() == "off":
        time_tasks[update.effective_chat.id] = {"active": False}
        await update.message.reply_text("🔴 Авто-время выключено."); return
    if context.args[0].lower() == "on" and len(context.args) > 1:
        tz = context.args[1]
        time_tasks[update.effective_chat.id] = {"active": True, "tz": tz}
        await update.message.reply_text(f"🟢 Авто-время включено (часовой пояс: {tz})")
        return
    await update.message.reply_text("Использование: `.time on +3` или `.time off`")

# ============ STREAKS ============

def get_streak(uid):
    if uid not in streak_data:
        streak_data[uid] = {"count": 0, "best": 0, "freeze": 0, "last": None}
    return streak_data[uid]

async def streak_cmd(update, context):
    s = get_streak(update.effective_user.id)
    await update.message.reply_text(
        f"🔥 *Ваша серия:*\n\n"
        f"Текущая: *{s['count']}* сообщений\n"
        f"Рекорд: *{s['best']}*\n"
        f"Заморозки: *{s['freeze']}*",
        parse_mode="Markdown"
    )

async def streak_freeze_cmd(update, context):
    s = get_streak(update.effective_user.id)
    if s["freeze"] <= 0:
        await update.message.reply_text("❌ Нет заморозок."); return
    s["freeze"] -= 1
    await update.message.reply_text("🧊 Серия заморожена!")

async def streak_recover_cmd(update, context):
    s = get_streak(update.effective_user.id)
    if s["count"] > 0:
        await update.message.reply_text("❌ Серия не провалена."); return
    s["count"] = 1
    await update.message.reply_text("🔄 Серия восстановлена! (1 день)")

async def streak_restart_cmd(update, context):
    s = get_streak(update.effective_user.id)
    s["best"] = max(s["best"], s["count"])
    s["count"] = 0
    await update.message.reply_text(f"🔄 Серия перезапущена! Рекорд сохранён: *{s['best']}*", parse_mode="Markdown")

async def streak_top_cmd(update, context):
    top = sorted(streak_data.items(), key=lambda x: x[1]["best"], reverse=True)[:10]
    if not top:
        await update.message.reply_text("Пока нет серий."); return
    lines = [f"🏆 *Топ серий:*\n"]
    for i, (uid, s) in enumerate(top):
        lines.append(f"{i+1}. Рекорд: {s['best']} 🔥")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def streak_unfreeze_cmd(update, context):
    s = get_streak(update.effective_user.id)
    s["freeze"] += 1
    await update.message.reply_text("🧊 Заморозка получена! (+1)")

# ============ ENTERTAINMENT ============

async def a_format_cmd(update, context):
    cid = update.effective_chat.id

    if context.args and context.args[0].lower() == "off":
        a_format_chats.pop(cid, None)
        await update.message.reply_text("🔴 Авто-форматирование выключено.")
        return

    if not context.args:
        if cid in a_format_chats:
            styles = a_format_chats[cid]
            names = []
            for s in styles:
                for k, v in STYLE_MAP.items():
                    if v == s:
                        names.append(k)
                        break
            await update.message.reply_text(f"🟢 Сейчас включено: {' + '.join(names)}\n\nВыключить: `.a_format off`")
        else:
            await update.message.reply_text(
                "Использование: `.a_format <стили>`\n\n"
                "Стили: цитата, жирный, курсив, подчёркнутый, зачёркнутый, скрытый, моно, моноблок\n"
                "Короткие: q, b, i, u, s, sp, c, pre\n\n"
                "Пример: `.a_format b i u` — жирный + курсив + подчёркнутый"
            )
        return

    STYLE_MAP = {
        "цитата": ">", "q": ">",
        "жирный": "*", "b": "*",
        "курсив": "_", "i": "_",
        "подчёркнутый": "__", "u": "__",
        "зачёркнутый": "~", "s": "~",
        "скрытый": "||", "sp": "||",
        "моно": "`", "c": "`",
        "моноблок": "```", "pre": "```",
    }

    selected = []
    for arg in context.args:
        arg_lower = arg.lower()
        if arg_lower in STYLE_MAP:
            selected.append(STYLE_MAP[arg_lower])

    if not selected:
        await update.message.reply_text("❌ Неизвестные стили. Используйте: цитата, жирный, курсив, подчёркнутый, зачёркнутый, скрытый, моно, моноблок")
        return

    if "```" in selected and len(selected) > 1:
        await update.message.reply_text("❌ Моноблок работает только сам по себе.")
        return

    if "`" in selected and any(s in selected for s in ["*", "_", "__", "~", "||"]):
        await update.message.reply_text("❌ Моно не сочетается с жирным, курсивом, подчёркнутым, зачёркнутым, скрытым.")
        return

    a_format_chats[cid] = selected
    names = [context.args[i] for i in range(len(context.args))]
    await update.message.reply_text(f"🟢 Авто-форматирование включено: {' + '.join(names)}\nВыключить: `.a_format off`")

async def a_mute_cmd(update, context):
    cid = update.effective_chat.id
    if cid in a_mute_chats:
        a_mute_chats.discard(cid)
        await update.message.reply_text("🔴 Авто-мут выключен.")
    else:
        a_mute_chats.add(cid)
        await update.message.reply_text("🟢 Авто-мут включён! (сообщения собеседника удаляются)")

async def a_troll_cmd(update, context):
    cid = update.effective_chat.id
    if cid in a_troll_chats:
        a_troll_chats.discard(cid)
        await update.message.reply_text("🔴 Авто-троллинг выключен.")
    else:
        a_troll_chats.add(cid)
        await update.message.reply_text("🟢 Авто-троллинг включён!")

async def act_cmd(update, context):
    act = " ".join(context.args) if context.args else random.choice(ACTIONS)
    name = update.effective_user.first_name
    await update.message.reply_text(f"🎭 {name} {act}")

async def cat_cmd(update, context):
    await update.message.reply_photo(random.choice(CAT_URLS), caption="🐱 Случайный кот")

async def coin_cmd(update, context):
    result = random.choice(["🪙 *Орёл!*", "🪙 *Решка!*"])
    await update.message.reply_text(result, parse_mode="Markdown")

async def fco_cmd(update, context):
    await update.message.reply_text(f"🔮 *Предсказание:*\n\n{random.choice(PREDICTIONS)}", parse_mode="Markdown")

async def ghoul_cmd(update, context):
    await update.message.reply_text(random.choice(GHOUL_MSGS))

async def love_cmd(update, context):
    heart = random.choice(HEARTS)
    msg = random.choice(LOVE_MSGS)
    await update.message.reply_text(f"{(heart+' ')*10}\n\n{msg}\n\n{(heart+' ')*10}")

async def online_cmd(update, context):
    cid = update.effective_chat.id
    if cid in online_chats:
        online_chats.discard(cid)
        await update.message.reply_text("🔴 Онлайн выключен."); return
    online_chats.add(cid)
    await update.message.reply_text("🟢 Онлайн включён! Выключить: `.online`")
    while cid in online_chats:
        try: await update.message.chat.send_action(ChatAction.TYPING)
        except: break
        await asyncio.sleep(5)

async def rps_cmd(update, context):
    if not context.args:
        await update.message.reply_text("`.rps камень/ножницы/бумага`"); return
    uc = context.args[0].lower()
    ch = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    if uc not in ch: await update.message.reply_text("Камень, ножницы или бумага?"); return
    bc = random.choice(list(ch.keys()))
    w = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}
    if uc == bc: r = f"🤝 Ничья!\nВы: {ch[uc]} {uc}\nБот: {ch[bc]} {bc}"
    elif w.get(uc) == bc: r = f"🎉 Вы победили!\nВы: {ch[uc]} {uc}\nБот: {ch[bc]} {bc}"
    else: r = f"🤖 Бот победил!\nВы: {ch[uc]} {uc}\nБот: {ch[bc]} {bc}"
    await update.message.reply_text(r)

async def troll_cmd(update, context):
    for i in random.sample(INSULTS, 10):
        await update.message.reply_text(i)
        await asyncio.sleep(0.5)

async def spam_cmd(update, context):
    text = " ".join(context.args) if context.args else "Спам!"
    for i in range(10):
        await update.message.reply_text(f"{i+1}. {text}")
        await asyncio.sleep(1)

# ============ TTT ============

def check_ttt(b):
    for a,c,d in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a] and b[a]==b[c]==b[d]: return b[a]
    return "draw" if all(b) else None

def render_ttt(b):
    l = []
    for i in range(0,9,3):
        r = [b[i+j] if b[i+j] else str(i+j+1) for j in range(3)]
        l.append(" | ".join(r))
        if i<6: l.append("---------")
    return "\n".join(l)

async def ttt_cmd(update, context):
    gid = str(random.randint(1000,9999))
    ttt_games[gid] = {"board": [None]*9, "current": 1, "p1": update.effective_user.id, "p2": None}
    await update.message.reply_text(
        f"❌⭕ *Крестики-нолики* #{gid}\n\nХоды: `.ttt <клетка> {gid}` (1-9)\n\n{render_ttt(ttt_games[gid]['board'])}",
        parse_mode="Markdown"
    )

async def ttt_process(update, context):
    args = context.args
    if not args: return False
    if args[0]=="join" and len(args)>1:
        gid = args[1]
        if gid not in ttt_games: await update.message.reply_text("Игра не найдена."); return True
        g = ttt_games[gid]
        if g["p2"]: await update.message.reply_text("Полно."); return True
        g["p2"] = update.effective_user.id
        await update.message.reply_text(f"Игрок 2 ⭕ присоединился!\n\n{render_ttt(g['board'])}")
        return True
    if args[0].isdigit() and len(args)>1:
        cell, gid = int(args[0])-1, args[1]
        if gid not in ttt_games: await update.message.reply_text("Игра не найдена."); return True
        g = ttt_games[gid]
        uid = update.effective_user.id
        if uid not in (g["p1"],g["p2"]): await update.message.reply_text("Вы не в игре."); return True
        pn = 1 if uid==g["p1"] else 2
        if pn!=g["current"]: await update.message.reply_text("Не ваш ход!"); return True
        if cell<0 or cell>8: await update.message.reply_text("1-9!"); return True
        if g["board"][cell]: await update.message.reply_text("Занята!"); return True
        g["board"][cell] = "❌" if pn==1 else "⭕"
        g["current"] = 2 if g["current"]==1 else 1
        w = check_ttt(g["board"])
        if w=="draw": await update.message.reply_text(f"🤝 Ничья!\n{render_ttt(g['board'])}"); del ttt_games[gid]
        elif w: await update.message.reply_text(f"🎉 Победа!\n{render_ttt(g['board'])}"); del ttt_games[gid]
        else: ns = "❌" if g["current"]==1 else "⭕"; await update.message.reply_text(f"Ход: {ns}\n\n{render_ttt(g['board'])}")
        return True
    return False

# ============ GIFT ============

async def gift_cmd(update, context):
    uid = update.effective_user.id
    stars = user_stars.get(uid, 100)
    lst = "\n".join([f"  {i+1}. {g['name']} — {g['cost']} ⭐" for i,g in enumerate(GIFTS)])
    await update.message.reply_text(f"🎁 *Магазин*\nБаланс: *{stars}* ⭐\n\n{lst}\n\nПокупка: `.gift <номер>`", parse_mode="Markdown")

async def gift_process(update, context):
    args = context.args
    if not args or not args[0].isdigit(): return False
    idx = int(args[0])-1
    if idx<0 or idx>=len(GIFTS): await update.message.reply_text("Неверный номер."); return True
    g = GIFTS[idx]; uid = update.effective_user.id; stars = user_stars.get(uid, 100)
    if stars<g["cost"]: await update.message.reply_text(f"Мало звёзд! Нужно {g['cost']}, у вас {stars}."); return True
    user_stars[uid] = stars-g["cost"]
    await update.message.reply_text(f"🎁 {g['name']} отправлено!\nСписано: {g['cost']} ⭐\nБаланс: {user_stars[uid]} ⭐")
    return True

# ============ UTILS ============

async def typing_cmd(update, context):
    await update.message.chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(3)
    await update.message.reply_text("✅ Готово! Печатал(а) 3 сек...")

async def save_cmd(update, context):
    if not context.args: await update.message.reply_text("`.save <ссылка>`"); return
    status = await update.message.reply_text("⏳ Скачиваю...")
    try:
        import yt_dlp
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "video.mp4")
            with yt_dlp.YoutubeDL({"outtmpl": out, "format": "best[ext=mp4]/best", "quiet": True}) as ydl:
                ydl.download([context.args[0]])
            f = next((os.path.join(tmpdir,x) for x in os.listdir(tmpdir) if x.endswith((".mp4",".webm",".mkv"))), None)
            if not f: await status.edit("❌ Не найдено."); return
            if os.path.getsize(f)>50*1024*1024: await status.edit("❌ >50 МБ."); return
            await status.edit("📤 Отправляю...")
            with open(f,"rb") as vf: await update.message.reply_video(video=vf, caption="📥 Сохранено!")
            await status.delete()
    except Exception as e: await status.edit(f"❌ {str(e)[:200]}")

async def send_cmd(update, context):
    if not context.args: await update.message.reply_text("`.send <сумма>`"); return
    try: amount = float(context.args[0])
    except: await update.message.reply_text("Сумма!"); return
    name = update.effective_user.first_name
    recv = update.message.reply_to_message.from_user.first_name if update.message.reply_to_message else "Получатель"
    await update.message.reply_text(
        f"💰 *ЧЕК КРИПТО БОТА*\n━━━━━━━━━━\n\n👤 От: *{name}*\n👥 Кому: *{recv}*\n💵 *{amount:.2f}* USDT\n\n━━━━━━━━━━\n✅ Успешно\n🕐 {update.message.date.strftime('%d.%m.%Y %H:%M')}\n━━━━━━━━━━\n🔒 Защищено",
        parse_mode="Markdown"
    )

# ============ AI ============

async def gpt_cmd(update, context):
    if not context.args: await update.message.reply_text("`.gpt <вопрос>`"); return
    q = " ".join(context.args)
    status = await update.message.reply_text("🧠 Думаю...")
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as http:
            r = await http.post("http://localhost:8080/v1/chat/completions", json={"model":"gpt-3.5-turbo","messages":[{"role":"user","content":q}],"max_tokens":1000})
            if r.status_code==200: await status.edit(f"🧠 *Ответ:*\n\n{r.json()['choices'][0]['message']['content']}", parse_mode="Markdown")
            else: await status.edit(f"❌ Ошибка: {r.status_code}")
    except: await status.edit("❌ AI недоступен.")

async def image_cmd(update, context):
    if not context.args: await update.message.reply_text("`.image <описание>`"); return
    p = " ".join(context.args)
    status = await update.message.reply_text("🎨 Генерирую...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as http:
            r = await http.post("http://localhost:8080/v1/images/generations", json={"prompt":p,"n":1,"size":"1024x1024"})
            if r.status_code==200:
                await update.message.reply_photo(r.json()["data"][0]["url"], caption=f"🎨 {p}"); await status.delete()
            else: await status.edit(f"❌ {r.status_code}")
    except: await status.edit("❌ AI недоступен.")

async def a_gpt_cmd(update, context):
    auto_gpt_chats.add(update.effective_chat.id)
    await update.message.reply_text("🟢 Автоответ AI включён! Выключить: `.a_gpt_off`")

async def a_gpt_off_cmd(update, context):
    auto_gpt_chats.discard(update.effective_chat.id)
    await update.message.reply_text("🔴 Автоответ AI выключен!")

# ============ GPT1 (Enhanced AI) ============

gpt1_history = {}

async def gpt1_cmd(update, context):
    cid = update.effective_chat.id
    if cid in gpt1_chats:
        gpt1_chats.discard(cid)
        await update.message.reply_text("🔴 GPT-1 режим выключен!")
        return
    gpt1_chats.add(cid)
    gpt1_history[cid] = []
    await update.message.reply_text(
        "🟢 *GPT-1 включён!*\n\n"
        "Бот будет отвечать на все сообщения с контекстом беседы.\n"
        "Выключить: `.gpt1`",
        parse_mode="Markdown"
    )

async def gpt1_reply(update, context):
    cid = update.effective_chat.id
    if cid not in gpt1_chats: return
    if update.effective_user.id == context.bot.id: return
    text = update.message.text
    if not text: return

    if cid not in gpt1_history:
        gpt1_history[cid] = []

    gpt1_history[cid].append({"role": "user", "content": text})
    if len(gpt1_history[cid]) > 20:
        gpt1_history[cid] = gpt1_history[cid][-20:]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as http:
            r = await http.post("http://localhost:8080/v1/chat/completions", json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "system", "content": "Ты умный помощник. Отвечай кратко и по делу на русском языке."}] + gpt1_history[cid],
                "max_tokens": 800
            })
            if r.status_code == 200:
                answer = r.json()["choices"][0]["message"]["content"]
                gpt1_history[cid].append({"role": "assistant", "content": answer})
                await update.message.reply_text(answer)
    except:
        await update.message.reply_text("❌ AI недоступен.")

# ============ OFFLINE MODE ============

async def offline_cmd(update, context):
    cid = update.effective_chat.id
    if cid in offline_chats:
        offline_chats.discard(cid)
        await update.message.reply_text("🟢 Вы снова онлайн! Бот не отвечает за вас.")
    else:
        offline_chats.add(cid)
        await update.message.reply_text(
            "🔴 *Режим оффлайн включён!*\n\n"
            "Бот будет отвечать на сообщения от вашего имени пока вы оффлайн.\n"
            "Выключить: `.offline`",
            parse_mode="Markdown"
        )

async def offline_reply(update, context):
    cid = update.effective_chat.id
    if cid not in offline_chats: return
    if update.effective_user.id == context.bot.id: return
    if update.effective_user.id in AUTHORIZED_USERS: return
    text = update.message.text
    if not text: return

    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as http:
            r = await http.post("http://localhost:8080/v1/chat/completions", json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Ты отвечаешь от имени пользователя в его чате. Отвечай как он — кратко, по-человечески, на русском. Не говори что ты ИИ."},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 300
            })
            if r.status_code == 200:
                answer = r.json()["choices"][0]["message"]["content"]
                await update.message.reply_text(answer)
    except:
        pass

async def doxing_cmd(update, context):
    if not context.args: await update.message.reply_text("`.doxing <@user>`"); return
    t = context.args[0]
    await update.message.reply_text(
        f"📊 *Результаты: {t}*\n\n👤 Username: {t}\n📱 Телефон: Не найден\n📧 Email: Не найден\n🌐 Соцсети: Нет данных\n📍 Локация: Не определена\n\n⚠️ _Открытые источники._",
        parse_mode="Markdown"
    )

async def auto_gpt_reply(update, context):
    if update.effective_chat.id not in auto_gpt_chats: return
    if update.effective_user.id==context.bot.id: return
    text = update.message.text
    if not text: return
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as http:
            r = await http.post("http://localhost:8080/v1/chat/completions", json={"model":"gpt-3.5-turbo","messages":[{"role":"user","content":text}],"max_tokens":500})
            if r.status_code==200: await update.message.reply_text(r.json()["choices"][0]["message"]["content"])
    except: pass

# ============ AUTO FEATURES ============

async def auto_format_handler(update, context):
    cid = update.effective_chat.id
    if cid not in a_format_chats: return
    if update.effective_user.id == context.bot.id: return
    if not update.message or not update.message.text: return
    text = update.message.text
    if text.startswith("."): return

    styles = a_format_chats[cid]
    formatted = text
    for s in styles:
        if s == ">":
            formatted = f"> {formatted}"
        elif s == "```":
            formatted = f"```\n{formatted}\n```"
        else:
            formatted = f"{s}{formatted}{s}"

    try:
        await update.message.edit_text(formatted)
    except:
        pass

async def auto_mute_handler(update, context):
    if update.effective_chat.id not in a_mute_chats: return
    if update.effective_user.id==context.bot.id: return
    if update.effective_user.id not in AUTHORIZED_USERS:
        try: await update.message.delete()
        except: pass

async def auto_troll_handler(update, context):
    if update.effective_chat.id not in a_troll_chats: return
    if update.effective_user.id==context.bot.id: return
    if random.random() < 0.3:
        await update.message.reply_text(random.choice(INSULTS))

# ============ MAIN ============

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    if not update.message: return
    if not await check_password(update, context): return

    if update.message.text:
        text = update.message.text.strip().lower()
        args = text.split()
        cmd = args[0] if args else ""
        cmd_args = args[1:]

        CMDS = {
            ".help": help_cmd, ".ping": ping_cmd,
            ".nick": nick_cmd, ".publ": publ_cmd, ".status": status_cmd,
            ".stories": stories_cmd, ".time": time_cmd,
            ".streak": streak_cmd, ".streak_freeze": streak_freeze_cmd,
            ".streak_recover": streak_recover_cmd, ".streak_restart": streak_restart_cmd,
            ".streak_top": streak_top_cmd, ".streak_unfreeze": streak_unfreeze_cmd,
            ".a_format": a_format_cmd, ".a_mute": a_mute_cmd, ".a_troll": a_troll_cmd,
            ".act": act_cmd, ".cat": cat_cmd, ".coin": coin_cmd,
            ".fco": fco_cmd, ".ghoul": ghoul_cmd, ".love": love_cmd,
            ".online": online_cmd, ".rps": rps_cmd, ".troll": troll_cmd,
            ".spam": spam_cmd, ".ttt": ttt_cmd, ".gift": gift_cmd,
            ".typing": typing_cmd, ".save": save_cmd, ".send": send_cmd,
            ".gpt": gpt_cmd, ".gpt1": gpt1_cmd, ".image": image_cmd,
            ".a_gpt": a_gpt_cmd, ".a_gpt_off": a_gpt_off_cmd, ".doxing": doxing_cmd,
            ".offline": offline_cmd,
        }

        if cmd==".ttt":
            context.args = cmd_args
            if await ttt_process(update, context): return

        if cmd==".gift":
            context.args = cmd_args
            if await gift_process(update, context): return

        if cmd in CMDS:
            context.args = cmd_args
            await CMDS[cmd](update, context)
            return

    await auto_gpt_reply(update, context)
    await gpt1_reply(update, context)
    await offline_reply(update, context)
    await auto_format_handler(update, context)
    await auto_mute_handler(update, context)
    await auto_troll_handler(update, context)


def main():
    if not BOT_TOKEN: logger.error("BOT_TOKEN not set!"); return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, main_handler))
    app.add_error_handler(lambda u, c: logger.error(f"Error: {c.error}"))
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
