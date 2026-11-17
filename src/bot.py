"""Запуск бота: long polling поверх сценария из config/scenario.json."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from src.scenario import (
    STATE_ASK_QUESTION,
    Answer,
    load_config,
    on_callback,
    on_text,
    start,
)
from src.telegram import TelegramClient, TelegramError

LOGGER = logging.getLogger("bot")
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "scenario.json"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def to_keyboard(answer: Answer) -> list[list[dict[str, str]]]:
    return [
        [{"text": button.text, "callback_data": button.data} for button in row]
        for row in answer.buttons
    ]


def user_label(update: dict[str, Any]) -> str:
    sender = update.get("from") or {}
    username = sender.get("username")
    if username:
        return f"@{username}"
    return sender.get("first_name") or str(sender.get("id", "гость"))


def handle_update(
    client: TelegramClient,
    update: dict[str, Any],
    config: dict[str, Any],
    states: dict[int, str],
) -> None:
    if "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        answer = on_callback(callback["data"] or "", config)
        states[chat_id] = answer.state
        client.answer_callback(callback["id"])
        client.send_message(chat_id, answer.text, to_keyboard(answer))
        return

    message = update.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    if chat_id is None:
        return

    text = message.get("text", "")
    state = states.get(chat_id, "start")
    if text.startswith("/start") or text.startswith("/help"):
        answer = start(config)
        states[chat_id] = answer.state
    else:
        answer = on_text(text, state, config, user=user_label(message))
        states[chat_id] = answer.state

    client.send_message(chat_id, answer.text, to_keyboard(answer))

    if answer.admin_notice:
        admin_id = config["business"].get("admin_chat_id")
        if admin_id:
            client.send_message(int(admin_id), answer.admin_notice)
        else:
            LOGGER.info("admin_chat_id не задан, уведомление: %s", answer.admin_notice)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_env(ROOT / ".env")

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        LOGGER.error("BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен от @BotFather.")
        return 1

    config = load_config(CONFIG_PATH)
    client = TelegramClient(token)
    states: dict[int, str] = {}
    offset: int | None = None

    LOGGER.info("Бот запущен, ожидаю сообщения")
    while True:
        try:
            updates = client.get_updates(offset)
        except TelegramError as error:
            LOGGER.warning("Опрос не удался: %s", error)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            try:
                handle_update(client, update, config, states)
            except TelegramError as error:
                LOGGER.warning("Не удалось обработать обновление: %s", error)
            except Exception:
                LOGGER.exception("Ошибка в обработчике")


if __name__ == "__main__":
    sys.exit(main())
