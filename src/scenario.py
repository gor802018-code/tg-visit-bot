"""Сценарий бота-визитки: чистая логика без обращений к Telegram."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STATE_START = "start"
STATE_ASK_QUESTION = "ask_question"

CALLBACK_SERVICE_PREFIX = "svc:"
CALLBACK_SLOT_PREFIX = "slot:"
CALLBACK_BACK = "back"
CALLBACK_ASK = "ask"


@dataclass(frozen=True)
class Button:
    text: str
    data: str


@dataclass
class Answer:
    text: str
    buttons: list[list[Button]] = field(default_factory=list)
    admin_notice: str | None = None
    state: str = STATE_START


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _services_menu(config: dict[str, Any]) -> list[list[Button]]:
    buttons = [
        [Button(service["title"], f"{CALLBACK_SERVICE_PREFIX}{service['id']}")]
        for service in config["services"]
    ]
    buttons.append([Button(config["texts"]["ask_button"], CALLBACK_ASK)])
    return buttons


def _find_service(config: dict[str, Any], service_id: str) -> dict[str, Any] | None:
    for service in config["services"]:
        if service["id"] == service_id:
            return service
    return None


def _format_welcome(config: dict[str, Any]) -> str:
    business = config["business"]
    return config["texts"]["welcome"].format(
        greeting=config["texts"]["greeting"],
        name=business["name"],
    )


def start(config: dict[str, Any]) -> Answer:
    return Answer(text=_format_welcome(config), buttons=_services_menu(config))


def on_callback(data: str, config: dict[str, Any]) -> Answer:
    texts = config["texts"]

    if data == CALLBACK_ASK:
        return Answer(text=texts["ask_question"], state=STATE_ASK_QUESTION)

    if data == CALLBACK_BACK:
        return Answer(
            text=f"{texts['choose_service']}",
            buttons=_services_menu(config),
        )

    if data.startswith(CALLBACK_SERVICE_PREFIX):
        service = _find_service(config, data[len(CALLBACK_SERVICE_PREFIX) :])
        if service is None:
            return Answer(text=texts["unknown"], buttons=_services_menu(config))
        buttons = [
            [Button(slot, f"{CALLBACK_SLOT_PREFIX}{service['id']}:{index}")]
            for index, slot in enumerate(service["slots"])
        ]
        buttons.append([Button(texts["back_to_services"], CALLBACK_BACK)])
        return Answer(
            text=texts["service_info"].format(
                title=service["title"],
                price=service["price"],
                duration=service["duration"],
            ),
            buttons=buttons,
        )

    if data.startswith(CALLBACK_SLOT_PREFIX):
        payload = data[len(CALLBACK_SLOT_PREFIX) :]
        service_id, _, index_text = payload.partition(":")
        service = _find_service(config, service_id)
        if service is None or not index_text.isdigit():
            return Answer(text=texts["unknown"], buttons=_services_menu(config))
        index = int(index_text)
        if index >= len(service["slots"]):
            return Answer(text=texts["unknown"], buttons=_services_menu(config))
        business = config["business"]
        return Answer(
            text=texts["slot_done"].format(
                title=service["title"],
                slot=service["slots"][index],
                address=business["address"],
                work_hours=business["work_hours"],
                phone=business["phone"],
            ),
            buttons=[[Button(texts["back_to_services"], CALLBACK_BACK)]],
        )

    return Answer(text=texts["unknown"], buttons=_services_menu(config))


def on_text(text: str, state: str, config: dict[str, Any], user: str = "гость") -> Answer:
    texts = config["texts"]
    if state != STATE_ASK_QUESTION:
        return Answer(text=texts["unknown"], buttons=_services_menu(config))

    question = text.strip()
    if not question:
        return Answer(text=texts["empty_question"], state=STATE_ASK_QUESTION)

    return Answer(
        text=texts["question_sent"],
        buttons=_services_menu(config),
        admin_notice=texts["notify_admin"].format(user=user, text=question),
    )
