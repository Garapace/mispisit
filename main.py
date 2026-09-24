import os

import vk_api
from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from database import (
    add_note,
    get_notes,
    delete_note,
    edit_note,
    search_notes,
)


load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

if not VK_TOKEN:
    raise RuntimeError("Не найден VK_TOKEN в файле .env")

if not VK_GROUP_ID:
    raise RuntimeError("Не найден VK_GROUP_ID в файле .env")

VK_GROUP_ID = int(VK_GROUP_ID)


def send_message(vk, peer_id, message):
    vk.messages.send(
        peer_id=peer_id,
        random_id=get_random_id(),
        message=message,
    )


def main():
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()

    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

    print("VK Notes Bot запущен!")

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue

        message = event.object.message

        text = message.get("text", "").strip()
        peer_id = message["peer_id"]
        vk_id = message["from_id"]

        print(f'Получено сообщение от {vk_id}: "{text}"')

        # Разделяем команду и аргументы
        command, _, args = text.partition(" ")
        command = command.lower()
        args = args.strip()

        # /start
        if command == "/start":
            send_message(
                vk,
                peer_id,
                "Привет! Я VK Notes Bot 👋\n\n"
                "Я умею сохранять твои заметки.\n\n"
                "/add текст - добавить заметку\n"
                "/list - показать заметки\n"
                "/edit ID текст - изменить заметку\n"
                "/delete ID - удалить заметку\n"
                "/search текст - найти заметки\n"
                "/help - помощь",
            )

        # /help
        elif command == "/help":
            send_message(
                vk,
                peer_id,
                "Доступные команды:\n\n"
                "/add текст - добавить заметку\n"
                "/list - показать все заметки\n"
                "/edit ID текст - изменить заметку\n"
                "/delete ID - удалить заметку\n"
                "/search текст - найти заметки",
            )

        # /add
        elif command == "/add":
            if not args:
                send_message(
                    vk,
                    peer_id,
                    "После /add нужно написать текст заметки.\n\n"
                    "Пример:\n"
                    "/add Купить молоко",
                )
                continue

            note_id = add_note(vk_id, args)

            send_message(
                vk,
                peer_id,
                f"✅ Заметка добавлена!\nID: {note_id}",
            )

        # /list
        elif command == "/list":
            notes = get_notes(vk_id)

            if not notes:
                send_message(
                    vk,
                    peer_id,
                    "📝 У тебя пока нет заметок.",
                )
                continue

            response = "📝 Твои заметки:\n\n"

            for note_id, note_text, created_at in notes:
                response += f"{note_id}. {note_text}\n"

            send_message(vk, peer_id, response)

        # /delete
        elif command == "/delete":
            if not args:
                send_message(
                    vk,
                    peer_id,
                    "Укажи ID заметки.\n\n"
                    "Пример:\n"
                    "/delete 3",
                )
                continue

            if not args.isdigit():
                send_message(
                    vk,
                    peer_id,
                    "ID заметки должен быть числом.\n\n"
                    "Пример:\n"
                    "/delete 3",
                )
                continue

            note_id = int(args)

            deleted = delete_note(vk_id, note_id)

            if deleted:
                send_message(
                    vk,
                    peer_id,
                    f"🗑 Заметка {note_id} удалена.",
                )
            else:
                send_message(
                    vk,
                    peer_id,
                    "Такой заметки нет или она тебе не принадлежит.",
                )

        # /edit
        elif command == "/edit":
            parts = args.split(maxsplit=1)

            if len(parts) < 2:
                send_message(
                    vk,
                    peer_id,
                    "Используй команду так:\n\n"
                    "/edit ID новый текст\n\n"
                    "Пример:\n"
                    "/edit 3 Купить хлеб",
                )
                continue

            note_id_text, new_text = parts

            if not note_id_text.isdigit():
                send_message(
                    vk,
                    peer_id,
                    "ID заметки должен быть числом.\n\n"
                    "Пример:\n"
                    "/edit 3 Купить хлеб",
                )
                continue

            if not new_text.strip():
                send_message(
                    vk,
                    peer_id,
                    "Новый текст заметки не может быть пустым.",
                )
                continue

            note_id = int(note_id_text)

            edited = edit_note(
                vk_id,
                note_id,
                new_text.strip(),
            )

            if edited:
                send_message(
                    vk,
                    peer_id,
                    f"✏️ Заметка {note_id} изменена.",
                )
            else:
                send_message(
                    vk,
                    peer_id,
                    "Такой заметки нет или она тебе не принадлежит.",
                )

        # /search
        elif command == "/search":
            if not args:
                send_message(
                    vk,
                    peer_id,
                    "Укажи текст для поиска.\n\n"
                    "Пример:\n"
                    "/search курсовая",
                )
                continue

            notes = search_notes(vk_id, args)

            if not notes:
                send_message(
                    vk,
                    peer_id,
                    f"🔎 По запросу «{args}» ничего не найдено.",
                )
                continue

            response = f"🔎 Результаты поиска «{args}»:\n\n"

            for note_id, note_text, created_at in notes:
                response += f"{note_id}. {note_text}\n"

            send_message(vk, peer_id, response)

        # Неизвестная команда
        else:
            send_message(
                vk,
                peer_id,
                "Неизвестная команда.\n\n"
                "Используй /help, чтобы посмотреть доступные команды.",
            )


if __name__ == "__main__":
    main()