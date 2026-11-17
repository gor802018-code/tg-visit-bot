"""Схема конфигурации бота: проверка JSON до запуска."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigError(RuntimeError):
    """Конфигурация не читается или не проходит проверку."""


class Business(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    work_hours: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    admin_chat_id: int | None = None


class Texts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    welcome: str
    greeting: str
    choose_service: str
    service_info: str
    slot_done: str
    ask_question: str
    question_sent: str
    back_to_services: str
    ask_button: str
    unknown: str
    empty_question: str
    notify_admin: str


class Service(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    price: int = Field(gt=0)
    duration: int = Field(gt=0)
    slots: list[str] = Field(min_length=1)


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business: Business
    texts: Texts
    services: list[Service] = Field(min_length=1)


def _describe(error: ValidationError) -> str:
    lines = ["Конфигурация заполнена неверно:"]
    for issue in error.errors():
        path = ".".join(str(part) for part in issue["loc"]) or "корень"
        lines.append(f"  {path}: {issue['msg']}")
    return "\n".join(lines)


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Файл конфигурации не найден: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"В файле {config_path.name} сломан JSON: строка {error.lineno}, колонка {error.colno}. "
            f"{error.msg}"
        ) from error

    try:
        scenario = Scenario.model_validate(raw)
    except ValidationError as error:
        raise ConfigError(_describe(error)) from error

    return scenario.model_dump()
