import os
import time
import random
import asyncio
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
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

unlocked_users = set()

INSULTS = [
    "Ты как обновление Windows — все игнорируют 😤", "Твои шутки как Wi-Fi — слабые 📶",
    "Ты как NullPointerException 💀", "Ты ошибка, которую Google не найдёт 🔎",
    "Ты как пинг — есть, но не нужен 📡", "Твои мозги как 404 🧠",
    "Ты как реклама — все хотят пропустить 📺", "Ты как ложный сигнал 📵",
    "Ты как синтаксическая ошибка 🐛", "Ты как spam — многословный 📧",
    "Твои идеи как кролики — размножаются, но бесполезны 🐇",
    "Ты как лаг в игре — раздражаешь всех 🎮",
]

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

# ============ COMMANDS ============

async def help_cmd(update, context):
    await update.message.reply_text("""
🤖 *Команды бота:*

`.gpt <вопрос>` – Вопрос нейросети
`.foto <запрос>` – Генерация фото
`.troll` – Спам оскорблениями
`.ping` – Задержка бота
`.help` – Помощь
    """, parse_mode="Markdown")

async def ping_cmd(update, context):
    start = time.time()
    msg = await update.message.reply_text("🏓 Пинг...")
    await msg.edit_text(f"🏓 Понг! ⏱️ {int((time.time()-start)*1000)}ms")

async def gpt_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.gpt <вопрос>`"); return
    question = " ".join(context.args)
    status = await update.message.reply_text("🧠 Думаю...")
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            r = await http.post(
                "https://text.pollinations.ai/",
                json={
                    "messages": [
                        {"role": "system", "content": "Ты умный помощник. Отвечай на русском языке кратко и по делу."},
                        {"role": "user", "content": question}
                    ],
                    "model": "openai"
                },
                headers={"Content-Type": "application/json"}
            )
            if r.status_code == 200:
                answer = r.text
                await status.edit(f"🧠 *Ответ:*\n\n{answer}", parse_mode="Markdown")
            else:
                await status.edit(f"❌ Ошибка: {r.status_code}")
    except Exception as e:
        await status.edit(f"❌ Ошибка: {str(e)[:200]}")

async def foto_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.foto <описание фото>`"); return
    prompt = " ".join(context.args)
    status = await update.message.reply_text("🎨 Генерирую фото...")
    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true"
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as http:
            r = await http.get(url)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
                with open("temp_foto.jpg", "wb") as f:
                    f.write(r.content)
                with open("temp_foto.jpg", "rb") as f:
                    await update.message.reply_photo(photo=f, caption=f"🎨 {prompt}")
                await status.delete()
                os.remove("temp_foto.jpg")
            else:
                await status.edit(f"❌ Не удалось сгенерировать.")
    except Exception as e:
        await status.edit(f"❌ Ошибка: {str(e)[:200]}")

async def troll_cmd(update, context):
    for insult in random.sample(INSULTS, min(10, len(INSULTS))):
        await update.message.reply_text(insult)
        await asyncio.sleep(0.5)

# ============ MAIN ============

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS and user_id not in ADMIN_USERS: return
    if not await check_password(update, context): return

    text = (update.message.text or "").strip().lower()
    args = text.split()
    cmd = args[0] if args else ""
    cmd_args = args[1:]

    CMDS = {
        ".help": help_cmd, ".ping": ping_cmd,
        ".gpt": gpt_cmd, ".foto": foto_cmd, ".troll": troll_cmd,
    }

    if cmd in CMDS:
        context.args = cmd_args
        await CMDS[cmd](update, context)

def main():
    if not BOT_TOKEN: logger.error("BOT_TOKEN not set!"); return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, main_handler))
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__": main()
