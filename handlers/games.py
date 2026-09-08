import random


async def rps_command(event, client, args):
    choices = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    user_choice = args[0].lower() if args else None

    if user_choice not in choices:
        await event.reply("🎮 *Камень-Ножницы-Бумага*\n\nИспользование: `.rps камень/ножницы/бумага`")
        return

    bot_choice = random.choice(list(choices.keys()))
    user_sym = choices[user_choice]
    bot_sym = choices[bot_choice]

    wins = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}

    if user_choice == bot_choice:
        text = f"🤝 Ничья!\n\nВы: {user_sym} {user_choice}\nБот: {bot_sym} {bot_choice}"
    elif wins.get(user_choice) == bot_choice:
        text = f"🎉 Вы победили!\n\nВы: {user_sym} {user_choice}\nБот: {bot_sym} {bot_choice}"
    else:
        text = f"🤖 Бот победил!\n\nВы: {user_sym} {user_choice}\nБот: {bot_sym} {bot_choice}"

    await event.reply(text)


TTC_SYMBOLS = {1: "❌", 2: "⭕"}


def check_ttt_winner(board):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


def render_board(board):
    lines = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            if board[idx]:
                row.append(board[idx])
            else:
                row.append(str(idx + 1))
        lines.append(" | ".join(row))
        if i < 6:
            lines.append("---------")
    return "\n".join(lines)


ttt_games = {}


async def ttt_command(event, client, args):
    game_id = str(random.randint(1000, 9999))
    board = [None] * 9

    ttt_games[game_id] = {
        "board": board,
        "current": 1,
        "player1": event.sender_id,
        "player2": None,
        "chat_id": event.chat_id,
    }

    await event.reply(
        f"❌⭕ *Крестики-нолики*\n\n"
        f"Игра #{game_id}\n"
        f"Игрок 1: Вы (❌)\n"
        f"Игрок 2: Ожидание...\n\n"
        f"Присоединиться: `.ttt join {game_id}`\n"
        f"Ход: `.ttt <номер клетки> {game_id}`\n\n"
        f"{render_board(board)}"
    )


async def ttt_process(event, client, args):
    if not args:
        return False

    if args[0] == "join" and len(args) > 1:
        game_id = args[1]
        if game_id not in ttt_games:
            await event.reply("❌ Игра не найдена.")
            return True

        game = ttt_games[game_id]
        if game["player2"]:
            await event.reply("❌ Игра уже полна.")
            return True
        if game["player1"] == event.sender_id:
            await event.reply("❌ Вы уже в игре.")
            return True

        game["player2"] = event.sender_id
        await event.reply(
            f"❌⭕ *Крестики-нолики*\n\n"
            f"Игра #{game_id}\n"
            f"Игрок 1: ❌\n"
            f"Игрок 2: ⭕ (Вы)\n\n"
            f"Ход: Игрок 1 (❌)\n"
            f"Чтобы сделать ход: `.ttt <номер клетки> {game_id}`\n\n"
            f"{render_board(game['board'])}"
        )
        return True

    if args[0].isdigit() and len(args) > 1:
        cell = int(args[0]) - 1
        game_id = args[1]

        if game_id not in ttt_games:
            await event.reply("❌ Игра не найдена.")
            return True

        game = ttt_games[game_id]

        if event.sender_id not in (game["player1"], game["player2"]):
            await event.reply("❌ Вы не в этой игре.")
            return True

        player_num = 1 if event.sender_id == game["player1"] else 2

        if player_num != game["current"]:
            await event.reply("❌ Сейчас не ваш ход!")
            return True

        if cell < 0 or cell > 8:
            await event.reply("❌ Номер клетки от 1 до 9.")
            return True

        if game["board"][cell] is not None:
            await event.reply("❌ Клетка уже занята!")
            return True

        game["board"][cell] = TTC_SYMBOLS[player_num]
        game["current"] = 2 if game["current"] == 1 else 1

        winner = check_ttt_winner(game["board"])

        if winner == "draw":
            await event.reply(f"🤝 Ничья!\n\n{render_board(game['board'])}")
            del ttt_games[game_id]
            return True
        elif winner:
            await event.reply(
                f"🎉 *Победа!*\n\n{render_board(game['board'])}\n\nИгра #{game_id} окончена."
            )
            del ttt_games[game_id]
            return True

        next_sym = TTC_SYMBOLS[game["current"]]
        await event.reply(
            f"❌⭕ *Крестики-нолики*\n\n"
            f"Игра #{game_id}\n\n"
            f"Ход: {next_sym}\n\n"
            f"{render_board(game['board'])}"
        )
        return True

    return False
