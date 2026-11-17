"""Минимальный клиент Telegram Bot API на стандартной библиотеке."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

API_ROOT = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT_SECONDS = 35


class TelegramError(RuntimeError):
    """Ответ Bot API с полем ok=false."""


class TelegramClient:
    def __init__(self, token: str) -> None:
        self._token = token

    def _call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        url = API_ROOT.format(token=self._token, method=method)
        data = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise TelegramError(f"{method}: HTTP {error.code} {detail}") from error
        except urllib.error.URLError as error:
            raise TelegramError(f"{method}: {error.reason}") from error

        if not body.get("ok"):
            raise TelegramError(f"{method}: {body.get('description', 'unknown error')}")
        return body["result"]

    def get_updates(self, offset: int | None, timeout: int = 30) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            payload["offset"] = offset
        return self._call("getUpdates", payload)

    def send_message(self, chat_id: int, text: str, keyboard: list[list[dict[str, str]]] | None = None) -> Any:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if keyboard:
            payload["reply_markup"] = {"inline_keyboard": keyboard}
        return self._call("sendMessage", payload)

    def answer_callback(self, callback_id: str) -> None:
        self._call("answerCallbackQuery", {"callback_query_id": callback_id})
