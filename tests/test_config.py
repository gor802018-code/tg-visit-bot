"""Проверка валидации конфигурации."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ConfigError, load_config  # noqa: E402

CONFIG_PATH = ROOT / "config" / "scenario.json"


class ValidConfigTest(unittest.TestCase):
    def test_project_config_is_valid(self):
        config = load_config(CONFIG_PATH)
        self.assertIn("business", config)
        self.assertTrue(config["services"])

    def test_prices_are_integers(self):
        config = load_config(CONFIG_PATH)
        for service in config["services"]:
            self.assertIsInstance(service["price"], int)
            self.assertGreater(service["price"], 0)


class BrokenConfigTest(unittest.TestCase):
    def _write(self, payload: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with handle:
            handle.write(payload)
        self.addCleanup(Path(handle.name).unlink)
        return Path(handle.name)

    def test_broken_json_reports_position(self):
        path = self._write('{"business": {')
        with self.assertRaises(ConfigError) as caught:
            load_config(path)
        self.assertIn("сломан JSON", str(caught.exception))

    def test_missing_field_is_reported(self):
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["business"].pop("address")
        path = self._write(json.dumps(raw, ensure_ascii=False))
        with self.assertRaises(ConfigError) as caught:
            load_config(path)
        self.assertIn("business.address", str(caught.exception))

    def test_negative_price_is_rejected(self):
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["services"][0]["price"] = -100
        path = self._write(json.dumps(raw, ensure_ascii=False))
        with self.assertRaises(ConfigError) as caught:
            load_config(path)
        self.assertIn("services.0.price", str(caught.exception))

    def test_empty_slots_are_rejected(self):
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["services"][0]["slots"] = []
        path = self._write(json.dumps(raw, ensure_ascii=False))
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_missing_file_is_reported(self):
        with self.assertRaises(ConfigError) as caught:
            load_config(ROOT / "config" / "nope.json")
        self.assertIn("не найден", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
