import asyncio
import os
import tempfile
from telethon.tl.types import ChatAction


online_chats = set()


async def typing_command(event, client, args):
    await client.send_chat_action(event.chat_id, ChatAction.typing)
    await asyncio.sleep(3)
    await event.reply("✅ Готово! Печатал(а) 3 секунды...")


async def online_command(event, client, args):
    chat_id = event.chat_id

    if chat_id in online_chats:
        online_chats.discard(chat_id)
        await event.reply("🔴 Режим онлайн-канала выключен.")
        return

    online_chats.add(chat_id)
    await event.reply(
        "🟢 *Режим онлайн-канала включён!*\n"
        "Бот будет имитировать присутствие.\n"
        "Чтобы выключить: `.online`"
    )

    while chat_id in online_chats:
        try:
            await client.send_chat_action(chat_id, ChatAction.typing)
        except Exception:
            break
        await asyncio.sleep(5)


async def send_command(event, client, args):
    if not args:
        await event.reply("Использование: `.send <сумма>`\nПример: `.send 2.5`")
        return

    try:
        amount = float(args[0])
    except ValueError:
        await event.reply("⚠️ Укажите корректную сумму!")
        return

    sender = "Вы"
    receiver = "Получатель"

    if event.is_reply:
        reply = await event.get_reply_message()
        if reply.sender:
            receiver = reply.sender.first_name or "Получатель"

    check_text = (
        f"💰 *ЧЕК КРИПТО БОТА*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Отправитель: *{sender}*\n"
        f"👥 Получатель: *{receiver}*\n"
        f"💵 Сумма: *{amount:.2f}* USDT\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✅ *Статус:* Успешно\n"
        f"🕐 Время: _{event.date.strftime('%d.%m.%Y %H:%M')}_\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🔒 Транзакция защищена"
    )

    await event.reply(check_text)


async def save_command(event, client, args):
    if not args:
        await event.reply(
            "Использование: `.save <ссылка>\n"
            "Поддерживаемые платформы: TikTok, YouTube Shorts, Instagram Reels, VK"
        )
        return

    url = args[0]
    status_msg = await event.reply("⏳ Скачиваю видео...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "video.mp4")

            import yt_dlp
            ydl_opts = {
                "outtmpl": output_path,
                "format": "best[ext=mp4]/best",
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            found_file = None
            for f in os.listdir(tmpdir):
                if f.endswith((".mp4", ".webm", ".mkv")):
                    found_file = os.path.join(tmpdir, f)
                    break

            if not found_file:
                await status_msg.edit("❌ Не удалось скачать видео.")
                return

            file_size = os.path.getsize(found_file)
            if file_size > 50 * 1024 * 1024:
                await status_msg.edit("❌ Видео слишком больше (>50 МБ).")
                return

            await status_msg.edit("📤 Отправляю видео...")
            await client.send_file(event.chat_id, found_file, caption="📥 Видео сохранено!")
            await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Ошибка: {str(e)[:200]}")
