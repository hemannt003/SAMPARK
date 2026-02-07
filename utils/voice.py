"""
Speech-to-Text (Whisper) and Text-to-Speech (gTTS) helpers.
"""

import io
import os
import tempfile
from pathlib import Path


# ── Speech-to-Text ──────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, lang: str = "hi") -> str:
    """
    Transcribe audio bytes to text using OpenAI Whisper API.
    Falls back to a placeholder if the API key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    # -- xAI provider: use Grok transcription endpoint if available
    provider = os.getenv("AI_PROVIDER", "openai")

    if not api_key and provider == "openai":
        return _placeholder_transcript(lang)

    try:
        from openai import OpenAI

        if provider == "xai":
            client = OpenAI(
                api_key=os.getenv("XAI_API_KEY", ""),
                base_url="https://api.x.ai/v1",
            )
        else:
            client = OpenAI(api_key=api_key)

        # Save audio to a temp file (Whisper expects a file)
        suffix = ".webm"
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
        return result.text.strip()

    except Exception as e:
        print(f"[STT Error] {e}")
        return _placeholder_transcript(lang)


def _placeholder_transcript(lang: str) -> str:
    """Demo placeholder when no API key is configured."""
    if lang == "hi":
        return "किसानों के लिए कोई योजना बताइए"
    return "Tell me about farmer schemes"


# ── Text-to-Speech ──────────────────────────────────────────────

def text_to_speech(text: str, lang: str = "hi") -> bytes:
    """
    Convert text to Hindi/English speech audio (MP3 bytes) using gTTS.
    Returns raw MP3 bytes that can be played via st.audio().
    """
    try:
        from gtts import gTTS

        tts_lang = "hi" if lang == "hi" else "en"
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        print(f"[TTS Error] {e}")
        return b""


def text_to_speech_openai(text: str, lang: str = "hi") -> bytes:
    """
    Alternative TTS using OpenAI's TTS API (higher quality).
    Requires OPENAI_API_KEY.
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=text,
        )
        return response.content

    except Exception as e:
        print(f"[OpenAI TTS Error] {e}")
        # Fallback to gTTS
        return text_to_speech(text, lang)
