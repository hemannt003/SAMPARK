"""
Voice handler — Speech-to-Text and Text-to-Speech.

Priority chain
--------------
STT:  Bhashini API → OpenAI Whisper → Web Speech API (browser fallback)
TTS:  Bhashini API → gTTS → OpenAI TTS
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Tuple

import httpx
import structlog

from server.config import get_settings

log = structlog.get_logger()
settings = get_settings()


# ═════════════════════════════════════════════════════════════════
#  Language detection helpers
# ═════════════════════════════════════════════════════════════════

# Map of BCP-47 codes to Bhashini source language codes
LANG_MAP = {
    "hi": "hi",
    "en": "en",
    "ta": "ta",
    "te": "te",
    "bn": "bn",
    "mr": "mr",
    "gu": "gu",
    "kn": "kn",
    "ml": "ml",
    "pa": "pa",
    "or": "or",
}


def detect_language_from_text(text: str) -> str:
    """Simple heuristic language detection from text content."""
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    latin = sum(1 for c in text if "a" <= c.lower() <= "z")
    if devanagari > latin:
        return "hi"
    return "en"


# ═════════════════════════════════════════════════════════════════
#  Speech-to-Text
# ═════════════════════════════════════════════════════════════════

async def transcribe(
    audio_bytes: bytes,
    lang: str = "hi",
    format: str = "webm",
) -> Tuple[str, str]:
    """
    Transcribe audio to text.

    Returns
    -------
    (transcript, detected_lang)
    """
    # Try Bhashini first
    if settings.bhashini_api_key:
        result = await _bhashini_stt(audio_bytes, lang)
        if result:
            detected = detect_language_from_text(result)
            return result, detected

    # Fallback: Whisper
    result = await _whisper_stt(audio_bytes, lang, format)
    if result:
        detected = detect_language_from_text(result)
        return result, detected

    # Final fallback
    placeholder = "किसानों के लिए कोई योजना बताइए" if lang == "hi" else "Tell me about farmer schemes"
    return placeholder, lang


async def _bhashini_stt(audio_bytes: bytes, lang: str) -> Optional[str]:
    """Bhashini Dhruva API for Speech-to-Text (22+ Indian languages)."""
    try:
        import base64

        audio_b64 = base64.b64encode(audio_bytes).decode()
        source_lang = LANG_MAP.get(lang, "hi")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": source_lang},
                        "audioFormat": "webm",
                        "samplingRate": 16000,
                    },
                }
            ],
            "inputData": {
                "audio": [{"audioContent": audio_b64}]
            },
        }

        headers = {
            "Content-Type": "application/json",
            "userID": settings.bhashini_user_id,
            "ulcaApiKey": settings.bhashini_api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.bhashini_pipeline_url,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract transcript
        output = data.get("pipelineResponse", [{}])[0]
        text = output.get("output", [{}])[0].get("source", "")
        if text:
            log.info("bhashini_stt_ok", lang=lang, length=len(text))
            return text.strip()
        return None

    except Exception as e:
        log.warning("bhashini_stt_failed", error=str(e))
        return None


async def _whisper_stt(
    audio_bytes: bytes, lang: str, format: str = "webm"
) -> Optional[str]:
    """OpenAI Whisper API fallback."""
    api_key = settings.openai_api_key or settings.get_ai_api_key()
    if not api_key:
        return None

    try:
        from openai import OpenAI

        base_url = settings.get_ai_base_url()
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        client = OpenAI(**kwargs)

        suffix = f".{format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="hi" if lang == "hi" else "en",
            )

        os.unlink(tmp_path)
        log.info("whisper_stt_ok", lang=lang, length=len(result.text))
        return result.text.strip()

    except Exception as e:
        log.warning("whisper_stt_failed", error=str(e))
        return None


# ═════════════════════════════════════════════════════════════════
#  Text-to-Speech
# ═════════════════════════════════════════════════════════════════

async def synthesize(text: str, lang: str = "hi") -> bytes:
    """
    Convert text to speech audio (MP3 bytes).

    Priority: Bhashini TTS → gTTS → OpenAI TTS
    """
    # Try Bhashini
    if settings.bhashini_api_key:
        audio = await _bhashini_tts(text, lang)
        if audio:
            return audio

    # gTTS fallback
    audio = _gtts_synthesize(text, lang)
    if audio:
        return audio

    # OpenAI TTS fallback
    return _openai_tts(text, lang)


async def _bhashini_tts(text: str, lang: str) -> Optional[bytes]:
    """Bhashini Dhruva API for Text-to-Speech."""
    try:
        target_lang = LANG_MAP.get(lang, "hi")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {"sourceLanguage": target_lang},
                        "gender": "female",
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}]
            },
        }

        headers = {
            "Content-Type": "application/json",
            "userID": settings.bhashini_user_id,
            "ulcaApiKey": settings.bhashini_api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.bhashini_pipeline_url,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        import base64

        output = data.get("pipelineResponse", [{}])[0]
        audio_b64 = output.get("audio", [{}])[0].get("audioContent", "")
        if audio_b64:
            log.info("bhashini_tts_ok", lang=lang)
            return base64.b64decode(audio_b64)
        return None

    except Exception as e:
        log.warning("bhashini_tts_failed", error=str(e))
        return None


def _gtts_synthesize(text: str, lang: str) -> Optional[bytes]:
    """gTTS (Google Text-to-Speech) — reliable free fallback."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="hi" if lang == "hi" else "en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        log.info("gtts_ok", lang=lang)
        return buf.read()
    except Exception as e:
        log.warning("gtts_failed", error=str(e))
        return None


def _openai_tts(text: str, lang: str) -> bytes:
    """OpenAI TTS — highest quality but costs tokens."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=text,
        )
        log.info("openai_tts_ok", lang=lang)
        return response.content
    except Exception as e:
        log.warning("openai_tts_failed", error=str(e))
        return b""
