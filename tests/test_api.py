"""Tests for FastAPI endpoints — health check, chat, voice."""

import os
import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AI_PROVIDER", "openai")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_sampark.db")

from main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint should return 200 with status info."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "provider" in data


@pytest.mark.asyncio
async def test_chat_query_structure(client):
    """Chat endpoint should accept a query and return structured response."""
    resp = await client.post(
        "/api/chat/query",
        json={"message": "Tell me about farmer schemes", "lang": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "is_guided" in data
    assert "session_id" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_synthesize_endpoint(client):
    """TTS endpoint should accept text and return audio base64."""
    resp = await client.post(
        "/api/voice/synthesize",
        json={"text": "Hello", "lang": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_b64" in data
    assert "format" in data


@pytest.mark.asyncio
async def test_scheme_search(client):
    """Scheme search should return results string."""
    resp = await client.get("/api/schemes/search", params={"query": "farmer"})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_screen_analyze_disabled():
    """Screen analyze should respect feature flag."""
    # This test validates the endpoint exists and handles requests
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/screen/analyze",
            json={"image_b64": "dGVzdA==", "context": "test", "lang": "en"},
        )
        # Should return either 200 (if enabled) or 403 (if disabled)
        assert resp.status_code in (200, 403)
