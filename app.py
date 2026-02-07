"""
Sampark AI — Voice-first Government Scheme Assistant
Main Streamlit application.

Run:  streamlit run app.py
"""

import json
import os
import base64
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from utils.i18n import t
from utils.ai_engine import get_ai_response, analyze_screen_capture, check_if_guided_flow
from utils.voice import transcribe_audio, text_to_speech
from st_components.styles import inject_css

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sampark AI | समpark AI",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS
inject_css()

# ─────────────────────────────────────────────────────────────────
# Declare custom Streamlit components
# ─────────────────────────────────────────────────────────────────
COMP_DIR = Path(__file__).parent / "st_components"

_audio_recorder = components.declare_component(
    "audio_recorder",
    path=str(COMP_DIR / "audio_recorder"),
)

_screen_share = components.declare_component(
    "screen_share",
    path=str(COMP_DIR / "screen_share"),
)


def audio_recorder_component(lang: str = "hi", key: str = "mic"):
    """Big mic button that returns base64 audio when recording stops."""
    return _audio_recorder(lang=lang, key=key, default=None)


def screen_share_component(
    lang: str = "hi",
    auto_capture: bool = True,
    capture_interval: int = 8,
    command: str = "",
    key: str = "screen",
):
    """Screen sharing component. Returns JSON events (started/stopped/frame)."""
    return _screen_share(
        lang=lang,
        auto_capture=auto_capture,
        capture_interval=capture_interval,
        command=command,
        key=key,
        default=None,
    )


# ─────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "lang": "hi",
    "messages": [],        # [{role, content, audio_bytes}]
    "screen_sharing": False,
    "guide_context": "",   # What user is trying to do
    "awaiting_guide": False,
    "last_guidance": "",
    "guidance_count": 0,
    "audio_key": 0,        # Incremented to force re-render of audio component
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

lang = st.session_state.lang


# ─────────────────────────────────────────────────────────────────
# Sidebar — settings
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### " + t("settings", lang))

    # Language toggle
    lang_choice = st.radio(
        t("language", lang),
        options=["hi", "en"],
        format_func=lambda x: "हिन्दी" if x == "hi" else "English",
        index=0 if lang == "hi" else 1,
        horizontal=True,
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        lang = lang_choice
        st.rerun()

    st.divider()

    # AI provider
    provider_map = {"openai": "OpenAI (GPT-4o)", "xai": "xAI (Grok)", "google": "Google (Gemini)"}
    provider = st.selectbox(
        t("provider_label", lang),
        options=list(provider_map.keys()),
        format_func=lambda x: provider_map[x],
        index=0,
    )
    os.environ["AI_PROVIDER"] = provider

    # API key
    env_key_map = {"openai": "OPENAI_API_KEY", "xai": "XAI_API_KEY", "google": "GOOGLE_API_KEY"}
    existing_key = os.getenv(env_key_map[provider], "")
    api_key = st.text_input(
        t("api_key_label", lang),
        value=existing_key,
        type="password",
        help="Paste your API key here",
    )
    if api_key:
        os.environ[env_key_map[provider]] = api_key

    st.divider()

    # Clear chat
    if st.button(t("clear_chat", lang), use_container_width=True):
        st.session_state.messages = []
        st.session_state.screen_sharing = False
        st.session_state.awaiting_guide = False
        st.session_state.guide_context = ""
        st.session_state.last_guidance = ""
        st.rerun()

    st.divider()
    st.caption(t("about", lang))


# ─────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="app-header">
        <h1>{t('app_title', lang)}</h1>
        <p>{t('tagline', lang)}</p>
    </div>""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────
# Helper: add message to chat
# ─────────────────────────────────────────────────────────────────
def add_message(role: str, content: str, audio_bytes: bytes = b""):
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "audio_bytes": audio_bytes,
    })


def process_user_input(user_text: str):
    """Send user text through AI → add response → optionally offer screen guide."""
    add_message("user", user_text)

    with st.spinner(t("processing", lang)):
        # Build history for context
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]  # Exclude the just-added user msg
        ]

        ai_reply = get_ai_response(user_text, history, lang)

    # Generate TTS for the reply
    tts_bytes = text_to_speech(ai_reply, lang)
    add_message("assistant", ai_reply, tts_bytes)

    # Check if this response warrants screen-guided assistance
    if check_if_guided_flow(ai_reply):
        st.session_state.awaiting_guide = True
        st.session_state.guide_context = user_text


# ─────────────────────────────────────────────────────────────────
# Welcome message (first load)
# ─────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    welcome = t("welcome_msg", lang)
    welcome_audio = text_to_speech(welcome.replace("•", "").replace("\n", " "), lang)
    add_message("assistant", welcome, welcome_audio)


# ─────────────────────────────────────────────────────────────────
# Chat history display
# ─────────────────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    avatar = "🧑‍🌾" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(
            f'<div class="chat-msg">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
        if msg.get("audio_bytes"):
            st.audio(msg["audio_bytes"], format="audio/mp3")


# ─────────────────────────────────────────────────────────────────
# Screen Guide Offer (after multi-step AI response)
# ─────────────────────────────────────────────────────────────────
if st.session_state.awaiting_guide and not st.session_state.screen_sharing:
    st.markdown(
        f"""<div class="guide-offer-card">
            <h3>{t('guide_offer', lang)}</h3>
        </div>""",
        unsafe_allow_html=True,
    )

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button(t("guide_yes", lang), key="guide_yes", use_container_width=True):
            st.session_state.screen_sharing = True
            st.session_state.awaiting_guide = False
            st.rerun()
    with col_no:
        if st.button(t("guide_no", lang), key="guide_no", use_container_width=True):
            st.session_state.awaiting_guide = False
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# Screen Sharing — Active
# ─────────────────────────────────────────────────────────────────
if st.session_state.screen_sharing:
    st.markdown(
        f'<div class="guide-active-banner">{t("guide_active", lang)}</div>',
        unsafe_allow_html=True,
    )

    # Render the screen share component
    screen_data = screen_share_component(
        lang=lang,
        auto_capture=True,
        capture_interval=8,
        key="screen_share_main",
    )

    # Process events from the component
    if screen_data:
        try:
            event = json.loads(screen_data) if isinstance(screen_data, str) else screen_data
        except (json.JSONDecodeError, TypeError):
            event = {}

        event_type = event.get("event", "")

        if event_type == "stopped":
            st.session_state.screen_sharing = False
            st.session_state.last_guidance = ""
            add_message("assistant", t("guide_stopped", lang))
            st.rerun()

        elif event_type == "frame":
            image_b64 = event.get("image", "")
            if image_b64:
                with st.spinner(t("guide_analyzing", lang)):
                    guidance = analyze_screen_capture(
                        image_b64,
                        st.session_state.guide_context,
                        lang,
                    )

                if guidance and guidance != st.session_state.last_guidance:
                    st.session_state.last_guidance = guidance
                    st.session_state.guidance_count += 1

                    # Show guidance
                    st.markdown(
                        f'<div class="guidance-text">{guidance}</div>',
                        unsafe_allow_html=True,
                    )

                    # Speak the guidance
                    guidance_audio = text_to_speech(guidance, lang)
                    if guidance_audio:
                        st.audio(guidance_audio, format="audio/mp3", autoplay=True)

                    # Save to chat history
                    add_message("assistant", f"🖥️ {guidance}", guidance_audio)

        elif event_type == "error":
            st.warning(t("guide_permission", lang))
            st.session_state.screen_sharing = False

    # Stop sharing button (always visible during sharing)
    if st.button(t("guide_stop", lang), key="stop_sharing_btn"):
        st.session_state.screen_sharing = False
        st.session_state.last_guidance = ""
        add_message("assistant", t("guide_stopped", lang))
        st.rerun()

    # Voice commands hint
    st.caption(t("guide_voice_cmds", lang))


# ─────────────────────────────────────────────────────────────────
# Voice input — Big mic button
# ─────────────────────────────────────────────────────────────────
st.markdown("---")

st.markdown(
    f'<p style="text-align:center;font-size:1.1rem;color:#666;margin-bottom:4px;">'
    f'{t("talk", lang)}</p>',
    unsafe_allow_html=True,
)

audio_b64 = audio_recorder_component(
    lang=lang,
    key=f"mic_{st.session_state.audio_key}",
)

if audio_b64 and isinstance(audio_b64, str) and len(audio_b64) > 100:
    # Decode audio
    audio_bytes = base64.b64decode(audio_b64)

    # Transcribe
    with st.spinner(t("thinking", lang)):
        transcript = transcribe_audio(audio_bytes, lang)

    if transcript:
        st.markdown(
            f'<p style="text-align:center;font-size:1.05rem;color:#333;">'
            f'{t("you_said", lang)} <strong>"{transcript}"</strong></p>',
            unsafe_allow_html=True,
        )

        # Check for screen guide voice commands
        lower = transcript.lower()
        guide_next = any(w in lower for w in ["अगला", "next", "आगे"])
        guide_repeat = any(w in lower for w in ["दोबारा", "repeat", "again", "फिर से"])

        if st.session_state.screen_sharing and guide_repeat and st.session_state.last_guidance:
            # Repeat last guidance
            repeat_audio = text_to_speech(st.session_state.last_guidance, lang)
            st.audio(repeat_audio, format="audio/mp3", autoplay=True)
        else:
            # Normal query processing
            process_user_input(transcript)

        # Increment key to reset the recorder component
        st.session_state.audio_key += 1
        st.rerun()


# ─────────────────────────────────────────────────────────────────
# Text input — fallback for typing
# ─────────────────────────────────────────────────────────────────
user_text = st.chat_input(t("type_here", lang))
if user_text:
    process_user_input(user_text)
    st.rerun()


# ─────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="app-footer">{t("powered_by", lang)}</div>',
    unsafe_allow_html=True,
)
