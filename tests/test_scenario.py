"""Проверка сценария без Telegram."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import (  # noqa: E402
    CALLBACK_ASK,
    CALLBACK_BACK,
    STATE_ASK_QUESTION,
    STATE_START,
    load_config,
    on_callback,
    on_text,
    start,
)

CONFIG = load_config(ROOT / "config" / "scenario.json")


class StartTest(unittest.TestCase):
    def test_welcome_mentions_business_name(self):
        answer = start(CONFIG)
        self.assertIn(CONFIG["business"]["name"], answer.text)
        self.assertEqual(answer.state, STATE_START)

    def test_menu_has_every_service_and_question_button(self):
        answer = start(CONFIG)
        labels = [button.data for row in answer.buttons for button in row]
        for service in CONFIG["services"]:
            self.assertIn(f"svc:{service['id']}", labels)
        self.assertIn(CALLBACK_ASK, labels)


class ServiceTest(unittest.TestCase):
    def test_service_shows_price(self):
        service = CONFIG["services"][0]
        answer = on_callback(f"svc:{service['id']}", CONFIG)
        self.assertIn(str(service["price"]), answer.text)
        self.assertIn(service["title"], answer.text)

    def test_service_offers_slot_buttons(self):
        service = CONFIG["services"][0]
        answer = on_callback(f"svc:{service['id']}", CONFIG)
        labels = [button.text for row in answer.buttons for button in row]
        for slot in service["slots"]:
            self.assertIn(slot, labels)

    def test_service_buttons_contain_each_slot(self):
        service = CONFIG["services"][1]
        answer = on_callback(f"svc:{service['id']}", CONFIG)
        data = [button.data for row in answer.buttons for button in row]
        for index in range(len(service["slots"])):
            self.assertIn(f"slot:{service['id']}:{index}", data)

    def test_unknown_service_falls_back_to_menu(self):
        answer = on_callback("svc:nothing", CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["unknown"])
        self.assertTrue(answer.buttons)


class SlotTest(unittest.TestCase):
    def test_slot_confirms_visit_with_address(self):
        service = CONFIG["services"][0]
        answer = on_callback(f"slot:{service['id']}:0", CONFIG)
        self.assertIn(service["slots"][0], answer.text)
        self.assertIn(CONFIG["business"]["address"], answer.text)
        self.assertIn(service["title"], answer.text)

    def test_slot_out_of_range_is_safe(self):
        answer = on_callback("slot:haircut:99", CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["unknown"])

    def test_slot_without_index_is_safe(self):
        answer = on_callback("slot:haircut", CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["unknown"])


class QuestionTest(unittest.TestCase):
    def test_ask_button_switches_state(self):
        answer = on_callback(CALLBACK_ASK, CONFIG)
        self.assertEqual(answer.state, STATE_ASK_QUESTION)
        self.assertEqual(answer.text, CONFIG["texts"]["ask_question"])

    def test_question_is_forwarded_to_admin(self):
        answer = on_text("Работаете в воскресенье?", STATE_ASK_QUESTION, CONFIG, user="@client")
        self.assertEqual(answer.text, CONFIG["texts"]["question_sent"])
        self.assertIsNotNone(answer.admin_notice)
        self.assertIn("Работаете в воскресенье?", answer.admin_notice)
        self.assertIn("@client", answer.admin_notice)
        self.assertEqual(answer.state, STATE_START)

    def test_empty_question_keeps_state(self):
        answer = on_text("   ", STATE_ASK_QUESTION, CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["empty_question"])
        self.assertEqual(answer.state, STATE_ASK_QUESTION)

    def test_random_text_shows_menu(self):
        answer = on_text("привет", STATE_START, CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["unknown"])
        self.assertTrue(answer.buttons)


class NavigationTest(unittest.TestCase):
    def test_back_returns_service_menu(self):
        answer = on_callback(CALLBACK_BACK, CONFIG)
        self.assertIn(CONFIG["services"][0]["title"], [b.text for row in answer.buttons for b in row])

    def test_unknown_callback_is_safe(self):
        answer = on_callback("что-то", CONFIG)
        self.assertEqual(answer.text, CONFIG["texts"]["unknown"])


if __name__ == "__main__":
    unittest.main()
