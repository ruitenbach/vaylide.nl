"""AI-hulp met sleutel: de aanroep naar Anthropic (nagebootst). Zonder sleutel: vaste testteksten."""
from types import SimpleNamespace
from unittest import mock

from django.test import override_settings

from core.ai import AIUnavailable, RequestAssessment, ai_configured, assess_request, suggest_text

from .helpers import VaylideTestCase


def _text_response(text, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=text)])


class AIWithKeyTests(VaylideTestCase):
    def test_without_key_test_texts(self):
        self.assertFalse(ai_configured())
        result = suggest_text(field="welcome_text", occasion="bruiloft", content={"names": {"partner_1": "Anna", "partner_2": "Bram"}},
                              tone="warm", notes="", current="")
        self.assertEqual(result.source, "test")

    @override_settings(ANTHROPIC_API_KEY="sk-nagebootst", AI_ENABLED=True, AI_MODEL="claude-opus-5-5")
    def test_suggestion_calls_the_model_with_only_customer_facts(self):
        client = mock.Mock()
        client.beta.messages.create.return_value = _text_response("Welkom op onze bruiloft!")
        with mock.patch("core.ai._client", return_value=client):
            result = suggest_text(field="welcome_text", occasion="bruiloft", content={"names": {"partner_1": "Anna", "partner_2": "Bram"}},
                                  tone="warm", notes="in de tuin", current="")
        self.assertEqual((result.source, result.text), ("ai", "Welkom op onze bruiloft!"))
        kwargs = client.beta.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-opus-5-5")
        self.assertIn("Verzin geen namen", kwargs["system"])
        self.assertIn("in de tuin", kwargs["messages"][0]["content"])

    @override_settings(ANTHROPIC_API_KEY="sk-nagebootst", AI_ENABLED=True)
    def test_refusal_gives_a_friendly_message(self):
        client = mock.Mock()
        client.beta.messages.create.return_value = _text_response("", stop="refusal")
        with mock.patch("core.ai._client", return_value=client):
            with self.assertRaises(AIUnavailable):
                suggest_text(field="story", occasion="bruiloft", content={}, tone="warm", notes="", current="")

    @override_settings(ANTHROPIC_API_KEY="sk-nagebootst", AI_ENABLED=True)
    def test_request_assessment_is_structured(self):
        parsed = RequestAssessment(summary="Tweetalige uitnodiging.", fit="custom", approach="1. Navragen.", open_questions=["Welke taal?"])
        client = mock.Mock()
        client.beta.messages.parse.return_value = SimpleNamespace(stop_reason="end_turn", parsed_output=parsed)
        with mock.patch("core.ai._client", return_value=client):
            assessment, source = assess_request(subject="Engels", description="Kan het ook in het Engels?", context="")
        self.assertEqual((source, assessment.fit), ("ai", "custom"))
        self.assertIn("Doe nooit toezeggingen", client.beta.messages.parse.call_args.kwargs["system"])
