"""Tests for the AI engine — covers process_query, is_guided_flow, and RAG search."""

import os
import pytest

# Set a dummy key so config loads without errors
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AI_PROVIDER", "openai")

from server.ai_engine import (
    GUIDED_KEYWORDS,
    SYSTEM_PROMPTS,
    is_guided_flow,
    search_schemes,
)


class TestIsGuidedFlow:
    """Unit tests for the multi-step detection heuristic."""

    def test_response_with_steps_and_website(self):
        response = "Step 1: Go to pmkisan.gov.in. Step 2: Register."
        assert is_guided_flow(response) is True

    def test_response_with_hindi_steps(self):
        response = "चरण 1: वेबसाइट खोलें। चरण 2: फ़ॉर्म भरें।"
        assert is_guided_flow(response) is True

    def test_simple_response_not_guided(self):
        response = "PM Kisan gives ₹6000 per year."
        assert is_guided_flow(response) is False

    def test_greeting_not_guided(self):
        response = "Hello! How can I help you today?"
        assert is_guided_flow(response) is False

    def test_grievance_response_guided(self):
        response = "File your complaint on pgportal.gov.in. Step 1: Register. Step 2: Lodge grievance."
        assert is_guided_flow(response) is True


class TestSystemPrompts:
    """Verify system prompts exist and are pure language."""

    def test_hindi_prompt_exists(self):
        assert "hi" in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["hi"]) > 100

    def test_english_prompt_exists(self):
        assert "en" in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["en"]) > 100

    def test_hindi_prompt_has_devanagari(self):
        hindi = SYSTEM_PROMPTS["hi"]
        devanagari_count = sum(1 for c in hindi if "\u0900" <= c <= "\u097F")
        assert devanagari_count > 50, "Hindi prompt should contain Devanagari script"


class TestGuidedKeywords:
    """Verify keyword list is populated."""

    def test_keywords_not_empty(self):
        assert len(GUIDED_KEYWORDS) >= 10

    def test_keywords_include_hindi_and_english(self):
        has_hindi = any("\u0900" <= c <= "\u097F" for kw in GUIDED_KEYWORDS for c in kw)
        has_english = any("a" <= c.lower() <= "z" for kw in GUIDED_KEYWORDS for c in kw)
        assert has_hindi and has_english


class TestRAGSearch:
    """RAG search should gracefully handle missing index."""

    def test_search_returns_string(self):
        result = search_schemes("farmer scheme")
        assert isinstance(result, str)
