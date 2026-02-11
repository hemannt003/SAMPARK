"""
Sampark AI — Streamlit Frontend (v2)

Upgraded to call FastAPI backend for AI, voice, and screen analysis.
Falls back to direct module imports when backend is unavailable.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from pathlib import Path

import httpx
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

# ── Local imports (used as fallback when FastAPI is down) ───────
from utils.i18n import t as _t
from st_components.styles import inject_css

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ═════════════════════════════════════════════════════════════════
#  Page Config
# ═════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Sampark AI | समpark AI",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()

# PWA registration script
st.markdown(
    """<script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    }
    </script>""",
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════════
#  Custom components
# ═════════════════════════════════════════════════════════════════

COMP_DIR = Path(__file__).parent / "st_components"

_audio_recorder = components.declare_component(
    "audio_recorder",
    path=str(COMP_DIR / "audio_recorder"),
)

_screen_share = components.declare_component(
    "screen_share",
    path=str(COMP_DIR / "screen_share"),
)


# ═════════════════════════════════════════════════════════════════
#  Session State
# ═════════════════════════════════════════════════════════════════

_DEFAULTS = {
    "lang": "hi",
    "messages": [],
    "session_id": str(uuid.uuid4())[:12],
    "screen_sharing": False,
    "guide_context": "",
    "awaiting_guide": False,
    "last_guidance": "",
    "audio_key": 0,
    "backend_alive": True,
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

lang = st.session_state.lang


# ═════════════════════════════════════════════════════════════════
#  Backend communication helpers
# ═════════════════════════════════════════════════════════════════

def _api(method: str, path: str, **kwargs) -> dict | None:
    """Call FastAPI backend. Returns JSON dict or None on failure."""
    try:
        with httpx.Client(base_url=BACKEND_URL, timeout=60.0) as client:
            resp = getattr(client, method)(path, **kwargs)
            resp.raise_for_status()
            st.session_state.backend_alive = True
            return resp.json()
    except Exception:
        st.session_state.backend_alive = False
        return None


def api_chat(message: str, lang: str, history: list) -> dict:
    """Send chat query to FastAPI, fallback to local processing."""
    result = _api("post", "/api/chat/query", json={
        "message": message,
        "lang": lang,
        "session_id": st.session_state.session_id,
        "history": history[-10:],
    })
    if result:
        return result

    # Fallback: use local AI engine directly
    from server.ai_engine import process_query, is_guided_flow
    from utils.voice import text_to_speech

    reply = process_query(message, history[-10:], lang)
    audio = text_to_speech(reply, lang)
    audio_b64 = base64.b64encode(audio).decode() if audio else ""
    return {
        "reply": reply,
        "audio_b64": audio_b64,
        "is_guided": is_guided_flow(reply),
        "session_id": st.session_state.session_id,
    }


def api_transcribe(audio_bytes: bytes, lang: str) -> str:
    """Transcribe audio via FastAPI, fallback to local Whisper."""
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
            with open(tmp_path, "rb") as f:
                resp = client.post(
                    "/api/voice/transcribe",
                    files={"audio": ("audio.webm", f, "audio/webm")},
                    data={"lang": lang},
                )
            resp.raise_for_status()
            os.unlink(tmp_path)
            return resp.json().get("transcript", "")

    except Exception:
        from utils.voice import transcribe_audio
        return transcribe_audio(audio_bytes, lang)


def api_synthesize(text: str, lang: str) -> bytes:
    """TTS via FastAPI, fallback to local gTTS."""
    result = _api("post", "/api/voice/synthesize", json={"text": text, "lang": lang})
    if result and result.get("audio_b64"):
        return base64.b64decode(result["audio_b64"])

    from utils.voice import text_to_speech
    return text_to_speech(text, lang)


def api_screen_analyze(image_b64: str, context: str, lang: str) -> dict:
    """Analyse screenshot via FastAPI, fallback to local vision."""
    result = _api("post", "/api/screen/analyze", json={
        "image_b64": image_b64,
        "context": context,
        "lang": lang,
    })
    if result:
        return result

    from server.ai_engine import analyze_screen
    guidance = analyze_screen(image_b64, context, lang)
    audio = api_synthesize(guidance, lang)
    return {
        "guidance": guidance,
        "audio_b64": base64.b64encode(audio).decode() if audio else "",
    }


# ═════════════════════════════════════════════════════════════════
#  Helper: add message
# ═════════════════════════════════════════════════════════════════

def add_msg(role: str, content: str, audio_b64: str = ""):
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "audio_b64": audio_b64,
    })


def process_user_input(text: str):
    """Send user text to AI and add response to chat."""
    add_msg("user", text)

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]

    with st.spinner(_t("processing", lang)):
        result = api_chat(text, lang, history)

    add_msg("assistant", result["reply"], result.get("audio_b64", ""))

    if result.get("is_guided"):
        st.session_state.awaiting_guide = True
        st.session_state.guide_context = text


# ═════════════════════════════════════════════════════════════════
#  Sidebar
# ═════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### " + _t("settings", lang))

    lang_choice = st.radio(
        _t("language", lang),
        ["hi", "en"],
        format_func=lambda x: "हिन्दी" if x == "hi" else "English",
        index=0 if lang == "hi" else 1,
        horizontal=True,
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        lang = lang_choice
        st.rerun()

    st.divider()

    # Backend status
    status_icon = "🟢" if st.session_state.backend_alive else "🔴"
    st.caption(f"{status_icon} Backend: {BACKEND_URL}")

    if st.button(_t("clear_chat", lang), use_container_width=True):
        st.session_state.messages = []
        st.session_state.screen_sharing = False
        st.session_state.awaiting_guide = False
        st.session_state.guide_context = ""
        st.session_state.last_guidance = ""
        st.rerun()

    st.divider()
    st.caption(_t("about", lang))


# ═════════════════════════════════════════════════════════════════
#  Header
# ═════════════════════════════════════════════════════════════════

st.markdown(
    f"""<div class="app-header">
        <h1>{_t('app_title', lang)}</h1>
        <p>{_t('tagline', lang)}</p>
    </div>""",
    unsafe_allow_html=True,
)


# ═════════════════════════════════════════════════════════════════
#  Welcome message
# ═════════════════════════════════════════════════════════════════

if not st.session_state.messages:
    welcome = _t("welcome_msg", lang)
    welcome_audio = api_synthesize(welcome.replace("•", "").replace("\n", " "), lang)
    audio_b64 = base64.b64encode(welcome_audio).decode() if welcome_audio else ""
    add_msg("assistant", welcome, audio_b64)


# ═════════════════════════════════════════════════════════════════
#  Chat history
# ═════════════════════════════════════════════════════════════════

for msg in st.session_state.messages:
    avatar = "🧑‍🌾" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(f'<div class="chat-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("audio_b64"):
            try:
                st.audio(base64.b64decode(msg["audio_b64"]), format="audio/mp3")
            except Exception:
                pass


# ═════════════════════════════════════════════════════════════════
#  Screen Guide Offer
# ═════════════════════════════════════════════════════════════════

if st.session_state.awaiting_guide and not st.session_state.screen_sharing:
    st.markdown(
        f'<div class="guide-offer-card"><h3>{_t("guide_offer", lang)}</h3></div>',
        unsafe_allow_html=True,
    )
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button(_t("guide_yes", lang), key="gy", use_container_width=True):
            st.session_state.screen_sharing = True
            st.session_state.awaiting_guide = False
            st.rerun()
    with col_n:
        if st.button(_t("guide_no", lang), key="gn", use_container_width=True):
            st.session_state.awaiting_guide = False
            st.rerun()


# ═════════════════════════════════════════════════════════════════
#  Screen Sharing Active
# ═════════════════════════════════════════════════════════════════

if st.session_state.screen_sharing:
    st.markdown(
        f'<div class="guide-active-banner">{_t("guide_active", lang)}</div>',
        unsafe_allow_html=True,
    )

    screen_data = _screen_share(
        lang=lang,
        auto_capture=True,
        capture_interval=8,
        key="ss_main",
        default=None,
    )

    if screen_data:
        try:
            event = json.loads(screen_data) if isinstance(screen_data, str) else screen_data
        except (json.JSONDecodeError, TypeError):
            event = {}

        etype = event.get("event", "")

        if etype == "stopped":
            st.session_state.screen_sharing = False
            st.session_state.last_guidance = ""
            add_msg("assistant", _t("guide_stopped", lang))
            st.rerun()

        elif etype == "frame":
            image_b64 = event.get("image", "")
            if image_b64:
                with st.spinner(_t("guide_analyzing", lang)):
                    result = api_screen_analyze(
                        image_b64, st.session_state.guide_context, lang
                    )

                guidance = result.get("guidance", "")
                if guidance and guidance != st.session_state.last_guidance:
                    st.session_state.last_guidance = guidance
                    st.markdown(
                        f'<div class="guidance-text">{guidance}</div>',
                        unsafe_allow_html=True,
                    )
                    if result.get("audio_b64"):
                        st.audio(
                            base64.b64decode(result["audio_b64"]),
                            format="audio/mp3",
                            autoplay=True,
                        )
                    add_msg("assistant", f"🖥️ {guidance}", result.get("audio_b64", ""))

        elif etype == "error":
            st.warning(_t("guide_permission", lang))
            st.session_state.screen_sharing = False

    if st.button(_t("guide_stop", lang), key="stop_ss"):
        st.session_state.screen_sharing = False
        st.session_state.last_guidance = ""
        add_msg("assistant", _t("guide_stopped", lang))
        st.rerun()

    st.caption(_t("guide_voice_cmds", lang))


# ═════════════════════════════════════════════════════════════════
#  Voice Input
# ═════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    f'<p style="text-align:center;font-size:1.15rem;color:#666;">{_t("talk", lang)}</p>',
    unsafe_allow_html=True,
)

audio_b64 = _audio_recorder(lang=lang, key=f"mic_{st.session_state.audio_key}", default=None)

if audio_b64 and isinstance(audio_b64, str) and len(audio_b64) > 100:
    audio_bytes = base64.b64decode(audio_b64)

    with st.spinner(_t("thinking", lang)):
        transcript = api_transcribe(audio_bytes, lang)

    if transcript:
        st.markdown(
            f'<p style="text-align:center;font-size:1.05rem;">'
            f'{_t("you_said", lang)} <strong>"{transcript}"</strong></p>',
            unsafe_allow_html=True,
        )

        lower = transcript.lower()
        is_repeat = any(w in lower for w in ["दोबारा", "repeat", "again", "फिर से"])

        if st.session_state.screen_sharing and is_repeat and st.session_state.last_guidance:
            audio = api_synthesize(st.session_state.last_guidance, lang)
            st.audio(audio, format="audio/mp3", autoplay=True)
        else:
            process_user_input(transcript)

        st.session_state.audio_key += 1
        st.rerun()


# ═════════════════════════════════════════════════════════════════
#  Text Input
# ═════════════════════════════════════════════════════════════════

user_text = st.chat_input(_t("type_here", lang))
if user_text:
    process_user_input(user_text)
    st.rerun()


# ═════════════════════════════════════════════════════════════════
#  Footer
# ═════════════════════════════════════════════════════════════════

st.markdown(
    f'<div class="app-footer">{_t("powered_by", lang)}</div>',
    unsafe_allow_html=True,
)
