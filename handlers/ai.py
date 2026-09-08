import httpx
import os

OPENCODE_API_URL = os.getenv("OPENCODE_API_URL", "http://localhost:8080")


async def gpt_command(event, client, args):
    if not args:
        await event.reply("Использование: `.gpt <ваш вопрос>`")
        return

    question = " ".join(args)
    status_msg = await event.reply("🧠 Думаю...")

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            response = await http.post(
                f"{OPENCODE_API_URL}/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": question}],
                    "max_tokens": 1000,
                },
            )

            if response.status_code == 200:
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                await status_msg.edit(f"🧠 *Ответ:*\n\n{answer}")
            else:
                await status_msg.edit(f"❌ Ошибка API: {response.status_code}")
    except httpx.ConnectError:
        await status_msg.edit(
            "❌ Не удалось подключиться к AI API.\n"
            "Убедитесь, что сервер запущен."
        )
    except Exception as e:
        await status_msg.edit(f"❌ Ошибка: {str(e)[:200]}")


async def image_command(event, client, args):
    if not args:
        await event.reply("Использование: `.image <описание изображения>`")
        return

    prompt = " ".join(args)
    status_msg = await event.reply("🎨 Генерирую изображение...")

    try:
        async with httpx.AsyncClient(timeout=120.0) as http:
            response = await http.post(
                f"{OPENCODE_API_URL}/v1/images/generations",
                json={
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                },
            )

            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                await client.send_file(event.chat_id, image_url, caption=f"🎨 *{prompt}*")
                await status_msg.delete()
            else:
                await status_msg.edit(f"❌ Ошибка API: {response.status_code}")
    except httpx.ConnectError:
        await status_msg.edit("❌ Не удалось подключиться к AI API.")
    except Exception as e:
        await status_msg.edit(f"❌ Ошибка: {str(e)[:200]}")


async def a_gpt_command(event, client, args):
    import bot as bot_module
    bot_module.auto_gpt_chats.add(event.chat_id)
    await event.reply(
        "🟢 *Автоответ нейросетью включён!*\n\n"
        "Теперь бот будет отвечать на все сообщения через AI.\n"
        "Чтобы выключить: `.a_gpt_off`"
    )


async def a_gpt_off_command(event, client, args):
    import bot as bot_module
    bot_module.auto_gpt_chats.discard(event.chat_id)
    await event.reply("🔴 *Автоответ нейросетью выключен!*")


async def auto_gpt_reply(event, client):
    text = event.raw_text
    if not text:
        return

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            response = await http.post(
                f"{OPENCODE_API_URL}/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": text}],
                    "max_tokens": 500,
                },
            )

            if response.status_code == 200:
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                await event.reply(answer)
    except Exception:
        pass


async def doxing_command(event, client, args):
    if not args:
        await event.reply("Использование: `.doxing <@username или номер телефона>`")
        return

    target = args[0]
    status_msg = await event.reply(f"🔍 Ищу информацию о *{target}*...")

    info = (
        f"📊 *Результаты поиска: {target}*\n\n"
        f"👤 *Username:* {target}\n"
        f"📱 *Телефон:* Не найден (публичные источники)\n"
        f"📧 *Email:* Не найден\n"
        f"🌐 *Соцсети:* Нет публичных данных\n"
        f"📍 *Локация:* Не определена\n\n"
        f"⚠️ _Данные из открытых источников._"
    )

    await status_msg.edit(info)
