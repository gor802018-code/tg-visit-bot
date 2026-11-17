"""Прогон сценария в консоли: увидеть тексты и переходы без Telegram."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import (  # noqa: E402
    STATE_START,
    Answer,
    load_config,
    on_callback,
    on_text,
    start,
)


def show(answer: Answer) -> None:
    print()
    print("БОТ:", answer.text.replace("\n", "\n     "))
    for row in answer.buttons:
        print("     [ " + " | ".join(button.text for button in row) + " ]")
    if answer.admin_notice:
        print("     >> администратору:", answer.admin_notice.replace("\n", " "))


def main() -> None:
    config = load_config(ROOT / "config" / "scenario.json")
    state = STATE_START

    print("Проверка сценария. Пустая строка или q — выход.")
    show(start(config))

    while True:
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not command or command.lower() == "q":
            break

        if command.startswith("svc:") or command in {"back", "ask"} or command.startswith("slot:"):
            answer = on_callback(command, config)
        else:
            answer = on_text(command, state, config, user="@демо")

        state = answer.state
        show(answer)


if __name__ == "__main__":
    main()
