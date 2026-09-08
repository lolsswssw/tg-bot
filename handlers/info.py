import time


async def help_command(event, client, args):
    help_text = """
🤖 *Команды бота:*

🎮 *Развлечения:*
`.fco` – Предсказание на сегодня
`.ghoul` – Я гуля...
`.gift` – Отправить подарок за звёзды
`.love` – Красивая анимация сердца
`.rps` – Камень-Ножницы-Бумага
`.ttt` – Крестики-нолики
`.troll` – Спам случайными оскорблениями
`.spam <текст>` – Спам текстом 10 раз

⚡ *Утилиты:*
`.online` – Имитация вечного онлайн-канала
`.save <ссылка>` – Сохранить видео
`.send <сумма>` – Фейковый чек Крипто Бота
`.typing` – Анимация печати текста

🧠 *AI функции:*
`.gpt <вопрос>` – Вопрос нейросети
`.image <запрос>` – Генерация изображения
`.a_gpt` – Включить автоответ нейросетью
`.a_gpt_off` – Выключить автоответ
`.doxing <юзер/номер>` – Поиск информации

📊 *Информация:*
`.help` – Это сообщение
`.ping` – Задержка ответа бота
    """
    await event.reply(help_text)


async def ping_command(event, client, args):
    start = time.time()
    msg = await event.reply("🏓 Пинг...")
    end = time.time()
    delay = int((end - start) * 1000)
    await msg.edit(f"🏓 Понг! ⏱️ {delay}ms")
