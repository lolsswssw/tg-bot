import os
import time
import random
import asyncio
import logging
import json
import requests
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
vid_states = {}

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
`.vid` – Генерация видео из фото
`.troll` – Спам оскорблениями
`.ping` – Задержка бота
`.help` – Помощь
    """, parse_mode="Markdown")

async def ping_cmd(update, context):
    start = time.time()
    msg = await update.message.reply_text("🏓 Пинг...")
    await msg.edit_text(f"🏓 Понг! ⏱️ {int((time.time()-start)*1000)}ms")

def _gpt_request(question):
    r = requests.post(
        "https://text.pollinations.ai/openai",
        json={"model": "openai", "messages": [{"role": "user", "content": question}], "max_tokens": 800},
        timeout=120
    )
    data = r.json()
    msg = data.get("choices", [{}])[0].get("message", {})
    return msg.get("content", "") or msg.get("reasoning", "Нет ответа.")

def _foto_request(prompt):
    encoded = prompt.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&enhance=true&nologo=true"
    r = requests.get(url, timeout=120)
    return r.content

def _vid_request(photo_path, prompt):
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    with open(photo_path, "rb") as f:
        img_bytes = f.read()

    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-video-diffusion-image-to-video"
    r = requests.post(API_URL, headers=headers, data=img_bytes, timeout=300)

    if r.status_code == 200:
        out_path = "temp_video.mp4"
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path

    if r.status_code == 503:
        import time
        time.sleep(30)
        r = requests.post(API_URL, headers=headers, data=img_bytes, timeout=300)
        if r.status_code == 200:
            out_path = "temp_video.mp4"
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path

    API_URL2 = "https://router.huggingface.co/hf-inference/models/damo-vilab/text-to-video-ms-1.7b"
    r2 = requests.post(API_URL2, headers=headers, json={"inputs": prompt}, timeout=300)
    if r2.status_code == 200:
        out_path = "temp_video.mp4"
        with open(out_path, "wb") as f:
            f.write(r2.content)
        return out_path

    raise Exception(f"API error: {r.status_code} {r.text[:200]}")

async def gpt_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.gpt <вопрос>`"); return
    question = " ".join(context.args)
    status = await update.message.reply_text("🧠 Думаю...")
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, _gpt_request, question)
        try: await status.delete()
        except: pass
        await update.message.reply_text(answer[:4000])
    except Exception as e:
        try: await status.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

async def foto_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Использование: `.foto <описание фото>`"); return
    prompt = " ".join(context.args)
    status = await update.message.reply_text("🎨 Генерирую фото...")
    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    try:
        loop = asyncio.get_event_loop()
        img_data = await loop.run_in_executor(None, _foto_request, prompt)
        try: await status.delete()
        except: pass
        if len(img_data) > 1000:
            with open("temp_foto.jpg", "wb") as f:
                f.write(img_data)
            with open("temp_foto.jpg", "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"🎨 {prompt}")
            os.remove("temp_foto.jpg")
        else:
            await update.message.reply_text("❌ Не удалось.")
    except Exception as e:
        try: await status.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

async def vid_cmd(update, context):
    uid = update.effective_user.id
    vid_states[uid] = {"step": "wait_photo"}
    await update.message.reply_text("📹 Отправьте фото для создания видео:")

async def troll_cmd(update, context):
    for insult in random.sample(INSULTS, min(10, len(INSULTS))):
        await update.message.reply_text(insult)
        await asyncio.sleep(0.5)

# ============ VID STATE HANDLER ============

async def handle_vid_photo(update, context):
    uid = update.effective_user.id
    state = vid_states.get(uid)
    if not state or state["step"] != "wait_photo":
        return False

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_path = f"vid_photo_{uid}.jpg"
    await file.download_to_drive(photo_path)

    vid_states[uid] = {"step": "wait_prompt", "photo": photo_path}
    await update.message.reply_text("✅ Фото получено! Теперь напишите промт (описание движения):")
    return True

async def handle_vid_prompt(update, context):
    uid = update.effective_user.id
    state = vid_states.get(uid)
    if not state or state["step"] != "wait_prompt":
        return False

    prompt = update.message.text
    photo_path = state["photo"]
    del vid_states[uid]

    status = await update.message.reply_text("🎬 Создаю видео...")
    await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
    try:
        loop = asyncio.get_event_loop()
        video_path = await loop.run_in_executor(None, _vid_request, photo_path, prompt)
        try: await status.delete()
        except: pass

        if os.path.exists(video_path) and os.path.getsize(video_path) > 1000:
            with open(video_path, "rb") as vf:
                await update.message.reply_video(video=vf, caption=f"🎬 {prompt}")
            os.remove(video_path)
        else:
            await update.message.reply_text("❌ Не удалось создать видео.")
    except Exception as e:
        try: await status.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

    if os.path.exists(photo_path):
        os.remove(photo_path)
    return True

# ============ MAIN ============

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS and user_id not in ADMIN_USERS: return
    if not await check_password(update, context): return

    if update.message.photo and not update.message.text:
        if await handle_vid_photo(update, context): return

    text = (update.message.text or "").strip().lower()
    args = text.split()
    cmd = args[0] if args else ""
    cmd_args = args[1:]

    if vid_states.get(user_id, {}).get("step") == "wait_prompt":
        if await handle_vid_prompt(update, context): return

    CMDS = {
        ".help": help_cmd, ".ping": ping_cmd,
        ".gpt": gpt_cmd, ".foto": foto_cmd, ".vid": vid_cmd, ".troll": troll_cmd,
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
