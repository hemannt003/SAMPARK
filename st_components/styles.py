"""
Custom CSS injection for the Streamlit app.
WhatsApp-style chat, big fonts, saffron/green theme, mobile friendly.
"""

import streamlit as st


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
/* ── Import Devanagari font ─────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

/* ── Global overrides ───────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide Streamlit's default header/footer for cleaner mobile look */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8F6B 100%);
    height: 0px;
}

/* ── App header ─────────────────────────────────────────────── */
.app-header {
    text-align: center;
    padding: 16px 8px 8px;
}
.app-header h1 {
    font-size: 2.4rem;
    font-weight: 700;
    color: #FF6B35;
    margin-bottom: 4px;
}
.app-header p {
    font-size: 1.1rem;
    color: #666;
    margin: 0;
}

/* ── Chat container ─────────────────────────────────────────── */
.chat-container {
    max-height: 55vh;
    overflow-y: auto;
    padding: 12px 4px;
    scroll-behavior: smooth;
}

/* ── Chat bubbles (WhatsApp-style) ──────────────────────────── */
.chat-msg {
    font-size: 1.15rem !important;
    line-height: 1.65 !important;
    word-wrap: break-word;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
[data-testid="stChatMessage"]:has(img[alt="🧑‍🌾"]) {
    background: #DCF8C6 !important;
    border-radius: 16px 16px 4px 16px !important;
    margin: 8px 0 8px 40px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
[data-testid="stChatMessage"]:has(img[alt="🤖"]) {
    background: #FFFFFF !important;
    border-radius: 16px 16px 16px 4px !important;
    margin: 8px 40px 8px 0 !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    border: 1px solid #F0F0F0;
}

/* ── Big talk/mic button ────────────────────────────────────── */
.big-talk-btn {
    display: flex;
    justify-content: center;
    margin: 20px auto 10px;
}
.big-talk-btn button,
.stButton > button.talk-btn {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    padding: 20px 48px !important;
    border-radius: 60px !important;
    background: linear-gradient(135deg, #FF6B35 0%, #E55A2B 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 6px 24px rgba(255, 107, 53, 0.4) !important;
    transition: all 0.2s ease !important;
    min-width: 220px;
    letter-spacing: 1px;
}
.stButton > button.talk-btn:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 30px rgba(255, 107, 53, 0.5) !important;
}
.stButton > button.talk-btn:active {
    transform: scale(0.97);
}

/* ── Screen guide buttons ───────────────────────────────────── */
.guide-btn-yes button {
    font-size: 1.2rem !important;
    padding: 14px 28px !important;
    border-radius: 16px !important;
    background: #2E7D32 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}
.guide-btn-no button {
    font-size: 1.2rem !important;
    padding: 14px 28px !important;
    border-radius: 16px !important;
    background: #F5F5F5 !important;
    color: #333 !important;
    border: 2px solid #DDD !important;
    font-weight: 600 !important;
}
.guide-btn-stop button {
    font-size: 1.1rem !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    background: #D32F2F !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}

/* ── Screen guide active banner ─────────────────────────────── */
.guide-active-banner {
    background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
    border: 2px solid #4CAF50;
    border-radius: 16px;
    padding: 16px 20px;
    text-align: center;
    font-size: 1.15rem;
    font-weight: 600;
    color: #2E7D32;
    margin: 12px 0;
    animation: guide-pulse 2s infinite;
}
@keyframes guide-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(76,175,80,0.3); }
    50% { box-shadow: 0 0 0 10px rgba(76,175,80,0); }
}

/* ── Guidance text (large and clear) ────────────────────────── */
.guidance-text {
    background: #FFFDE7;
    border: 2px solid #FFC107;
    border-radius: 16px;
    padding: 20px;
    font-size: 1.25rem;
    line-height: 1.7;
    color: #333;
    margin: 12px 0;
}
.guidance-text strong {
    color: #E65100;
}

/* ── Screen guide offer card ────────────────────────────────── */
.guide-offer-card {
    background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
    border: 2px solid #64B5F6;
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
}
.guide-offer-card h3 {
    font-size: 1.3rem;
    color: #1565C0;
    margin-bottom: 16px;
}

/* ── Audio player ───────────────────────────────────────────── */
audio {
    width: 100% !important;
    max-width: 340px;
    margin: 8px 0;
}

/* ── Status badges ──────────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.95rem;
    font-weight: 600;
    text-align: center;
}
.status-listening {
    background: #FFEBEE;
    color: #D32F2F;
    animation: blink 1s infinite;
}
.status-thinking {
    background: #FFF3E0;
    color: #E65100;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ── Footer ─────────────────────────────────────────────────── */
.app-footer {
    text-align: center;
    padding: 12px;
    font-size: 0.85rem;
    color: #999;
    margin-top: 20px;
}

/* ── Sidebar ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #FFF8F0;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 1.1rem !important;
    font-weight: 600;
}

/* ── Text input ─────────────────────────────────────────────── */
[data-testid="stChatInput"] textarea,
.stTextInput input {
    font-size: 1.1rem !important;
    border-radius: 24px !important;
    padding: 12px 20px !important;
    border: 2px solid #E0E0E0 !important;
}
[data-testid="stChatInput"] textarea:focus,
.stTextInput input:focus {
    border-color: #FF6B35 !important;
    box-shadow: 0 0 0 3px rgba(255,107,53,0.15) !important;
}

/* ── Mobile adjustments ─────────────────────────────────────── */
@media (max-width: 768px) {
    .app-header h1 { font-size: 2rem; }
    .chat-msg { font-size: 1.05rem !important; }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    [data-testid="stChatMessage"]:has(img[alt="🧑‍🌾"]) {
        margin: 6px 0 6px 16px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has(img[alt="🤖"]) {
        margin: 6px 16px 6px 0 !important;
    }

    .stButton > button.talk-btn {
        font-size: 1.3rem !important;
        padding: 16px 36px !important;
        min-width: 180px;
    }
}

/* ── Scrollbar styling ──────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CCC; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #AAA; }

/* ── Expander (for screen share component) ──────────────────── */
.streamlit-expanderContent {
    border: none !important;
    padding: 0 !important;
}
</style>
"""
