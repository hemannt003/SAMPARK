"""
AI Engine — multi-provider LLM (xAI Grok / OpenAI / Gemini) with RAG.

Responsibilities
----------------
* process_query   — text-only conversational AI with optional RAG context
* analyze_screen  — multimodal vision analysis for screen-guided assistance
* build_rag_index — create / refresh a FAISS vector store from scheme JSON
* search_schemes  — semantic search over the scheme corpus
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import structlog

from server.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# ── Paths ───────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEMES_FILE = DATA_DIR / "schemes.json"
FAISS_DIR = DATA_DIR / "faiss_index"


# ═════════════════════════════════════════════════════════════════
#  System Prompts — pure Hindi / pure English
# ═════════════════════════════════════════════════════════════════

SYSTEM_PROMPTS = {
    "hi": (
        "आप \"समpark AI\" हैं — भारत सरकार की योजनाओं के विशेषज्ञ सहायक।\n"
        "आपका विशेष ध्यान मध्य प्रदेश की योजनाओं पर है।\n\n"
        "नियम:\n"
        "1. केवल शुद्ध हिन्दी (देवनागरी) में उत्तर दें। अंग्रेज़ी शब्द न मिलाएँ।\n"
        "2. बहुत सरल शब्दों का प्रयोग करें — गाँव के व्यक्ति को समझाने जैसे।\n"
        "3. चरण हमेशा क्रमांकित (1, 2, 3…) लिखें।\n"
        "4. हर योजना के लिए बताएँ: पात्रता, लाभ, दस्तावेज़, आवेदन चरण, वेबसाइट।\n"
        "5. शिकायत निवारण (PG Portal, CM Helpline) में भी सहायता करें।\n"
        "6. स्रोत सदैव बताएँ (जैसे 'pmkisan.gov.in के अनुसार')।\n"
        "7. अस्वीकरण: \"यह जानकारी मार्गदर्शन हेतु है — अंतिम निर्णय सरकारी विभाग का होगा।\"\n"
        "8. यदि उत्तर में कई चरण हैं, अंत में पूछें: "
        "\"क्या आप चाहते हैं कि मैं आपकी स्क्रीन देखकर गाइड करूँ?\""
    ),
    "en": (
        "You are \"Sampark AI\" — an expert assistant for Indian government schemes.\n"
        "You have special focus on Madhya Pradesh schemes.\n\n"
        "Rules:\n"
        "1. Reply only in pure English. Do not mix Hindi words.\n"
        "2. Use very simple words — explain as if to someone with low literacy.\n"
        "3. Always number the steps (1, 2, 3…).\n"
        "4. For every scheme mention: eligibility, benefits, documents, steps, website.\n"
        "5. Also help with grievance redressal (PG Portal, CM Helpline).\n"
        "6. Always cite sources (e.g. 'as per pmkisan.gov.in').\n"
        "7. Disclaimer: \"This information is for guidance — final decision rests with the government.\"\n"
        "8. If the answer has multiple steps, ask at the end: "
        "\"Would you like me to guide you by seeing your screen?\""
    ),
}

SCREEN_GUIDE_PROMPTS = {
    "hi": (
        "आप कम डिजिटल साक्षरता वाले उपयोगकर्ता को उनकी स्क्रीन देखकर मार्गदर्शन कर रहे हैं।\n\n"
        "नियम:\n"
        "1. पहले बताएँ कि स्क्रीन पर क्या दिख रहा है (संक्षेप में)।\n"
        "2. फिर अगला कदम बहुत सरल हिन्दी में बताएँ।\n"
        "3. स्पष्ट दिशा-निर्देश दें: \"ऊपर दाईं तरफ़ हरा बटन दबाएँ\"।\n"
        "4. यदि कोई खाना भरना हो: \"आधार नंबर वाले खाने में 12 अंकों का नंबर भरें\"।\n"
        "5. यदि त्रुटि दिखे, सरल शब्दों में समझाएँ।\n"
        "6. एक समय में एक कदम। धैर्य से बात करें।\n"
        "7. यदि स्क्रीन पर कोई फ़ॉर्म दिखे, OCR से पढ़ें और बताएँ कौन-सा फ़ील्ड अधूरा या गलत है।"
    ),
    "en": (
        "You are guiding a low-digital-literacy user step-by-step by looking at their screen.\n\n"
        "Rules:\n"
        "1. First briefly describe what you see on the screen.\n"
        "2. Then explain the next step in very simple English.\n"
        "3. Give clear directions: \"Press the green button in the top-right corner\".\n"
        "4. If a field needs filling: \"In the Aadhaar box type your 12-digit number\".\n"
        "5. If there is an error, explain simply what went wrong.\n"
        "6. One step at a time. Be patient.\n"
        "7. If a form is visible, OCR-read it and tell which field is incomplete or wrong."
    ),
}

# Keywords that signal a multi-step response needing screen guidance
GUIDED_KEYWORDS = [
    "चरण", "step", "steps", "आवेदन", "apply", "register",
    "पंजीकरण", "फ़ॉर्म", "form", "वेबसाइट", "website",
    "पोर्टल", "portal", ".gov.in", ".nic.in",
    "शिकायत", "grievance", "complaint", "link", "लिंक",
]


# ═════════════════════════════════════════════════════════════════
#  OpenAI-compatible client (works for openai + xAI Grok)
# ═════════════════════════════════════════════════════════════════

def _openai_client():
    from openai import OpenAI

    kwargs: dict = {"api_key": settings.get_ai_api_key()}
    base = settings.get_ai_base_url()
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


# ═════════════════════════════════════════════════════════════════
#  RAG — FAISS vector store for scheme data
# ═════════════════════════════════════════════════════════════════

_faiss_store = None  # lazy singleton


def _load_faiss():
    """Load or build the FAISS index from scheme JSON."""
    global _faiss_store

    if _faiss_store is not None:
        return _faiss_store

    if not settings.enable_rag:
        return None

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings

        index_path = FAISS_DIR / "index.faiss"
        if index_path.exists():
            embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key or settings.get_ai_api_key()
            )
            _faiss_store = FAISS.load_local(
                str(FAISS_DIR), embeddings, allow_dangerous_deserialization=True
            )
            log.info("faiss_loaded", path=str(FAISS_DIR))
            return _faiss_store

        # Build from scratch
        return build_rag_index()

    except Exception as e:
        log.warning("faiss_load_failed", error=str(e))
        return None


def build_rag_index():
    """Build FAISS index from data/schemes.json and persist to disk."""
    global _faiss_store

    if not SCHEMES_FILE.exists():
        log.warning("schemes_file_missing", path=str(SCHEMES_FILE))
        return None

    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings

        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            schemes = json.load(f)

        # Flatten scheme data into searchable documents
        docs: List[str] = []
        for scheme in schemes:
            text = (
                f"Scheme: {scheme.get('name_en', '')} / {scheme.get('name_hi', '')}\n"
                f"Category: {scheme.get('category', '')}\n"
                f"State: {scheme.get('state', 'All India')}\n"
                f"Eligibility (EN): {scheme.get('eligibility_en', '')}\n"
                f"Eligibility (HI): {scheme.get('eligibility_hi', '')}\n"
                f"Benefits (EN): {scheme.get('benefit_en', '')}\n"
                f"Benefits (HI): {scheme.get('benefit_hi', '')}\n"
                f"Documents: {', '.join(scheme.get('documents_en', []))}\n"
                f"Website: {scheme.get('website', '')}\n"
                f"Helpline: {scheme.get('helpline', '')}\n"
            )
            docs.append(text)

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.create_documents(docs)

        embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key or settings.get_ai_api_key()
        )
        store = FAISS.from_documents(chunks, embeddings)

        FAISS_DIR.mkdir(parents=True, exist_ok=True)
        store.save_local(str(FAISS_DIR))
        _faiss_store = store
        log.info("faiss_built", num_chunks=len(chunks))
        return store

    except Exception as e:
        log.warning("faiss_build_failed", error=str(e))
        return None


def search_schemes(query: str, k: int = 3) -> str:
    """Semantic search for relevant scheme information."""
    store = _load_faiss()
    if store is None:
        return ""
    try:
        results = store.similarity_search(query, k=k)
        return "\n---\n".join(doc.page_content for doc in results)
    except Exception as e:
        log.warning("faiss_search_error", error=str(e))
        return ""


# ═════════════════════════════════════════════════════════════════
#  Text query → AI response
# ═════════════════════════════════════════════════════════════════

def process_query(
    user_message: str,
    history: Optional[List[dict]] = None,
    lang: str = "hi",
    session_id: str = "",
) -> str:
    """
    Process a user text query and return the AI response.

    Parameters
    ----------
    user_message : str
    history : list of {role, content} dicts (last N turns)
    lang : 'hi' or 'en'
    session_id : for logging / context

    Returns
    -------
    str — the assistant's reply
    """
    history = history or []

    # Augment with RAG context
    rag_context = ""
    if settings.enable_rag:
        rag_context = search_schemes(user_message, k=3)

    provider = settings.ai_provider
    if provider == "google":
        return _google_text(user_message, history, lang, rag_context)
    return _openai_text(user_message, history, lang, rag_context)


def _openai_text(
    user_message: str,
    history: list,
    lang: str,
    rag_context: str,
) -> str:
    try:
        client = _openai_client()

        system = SYSTEM_PROMPTS[lang]
        if rag_context:
            system += (
                f"\n\nRelevant scheme data (use if helpful):\n{rag_context}"
            )

        messages = [{"role": "system", "content": system}]
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        resp = client.chat.completions.create(
            model=settings.get_model_name(vision=False),
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        log.error("openai_text_error", error=str(e))
        return _fallback(user_message, lang)


def _google_text(
    user_message: str,
    history: list,
    lang: str,
    rag_context: str,
) -> str:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)

        system = SYSTEM_PROMPTS[lang]
        if rag_context:
            system += f"\n\nRelevant scheme data:\n{rag_context}"

        model = genai.GenerativeModel(
            model_name=settings.get_model_name(),
            system_instruction=system,
        )

        hist_text = ""
        for m in history[-10:]:
            prefix = "User" if m["role"] == "user" else "Assistant"
            hist_text += f"{prefix}: {m['content']}\n"

        resp = model.generate_content(f"{hist_text}User: {user_message}\nAssistant:")
        return resp.text.strip()

    except Exception as e:
        log.error("google_text_error", error=str(e))
        return _fallback(user_message, lang)


# ═════════════════════════════════════════════════════════════════
#  Screen analysis (vision)
# ═════════════════════════════════════════════════════════════════

def analyze_screen(
    image_base64: str,
    context: str,
    lang: str = "hi",
) -> str:
    """
    Analyse a screenshot with a vision model and return guidance.

    Parameters
    ----------
    image_base64 : JPEG base64 (no prefix)
    context      : what the user is trying to do
    lang         : 'hi' or 'en'
    """
    provider = settings.ai_provider
    if provider == "google":
        return _google_vision(image_base64, context, lang)
    return _openai_vision(image_base64, context, lang)


def _openai_vision(image_base64: str, context: str, lang: str) -> str:
    try:
        client = _openai_client()

        ctx_msg = {
            "hi": f"उपयोगकर्ता यह कर रहा है: {context}\nस्क्रीन देखकर अगला कदम बताएँ।",
            "en": f"User is trying to: {context}\nLook at the screen and tell the next step.",
        }

        messages = [
            {"role": "system", "content": SCREEN_GUIDE_PROMPTS[lang]},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ctx_msg[lang]},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                ],
            },
        ]

        resp = client.chat.completions.create(
            model=settings.get_model_name(vision=True),
            messages=messages,
            max_tokens=500,
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        log.error("vision_error", error=str(e))
        return _vision_fallback(lang)


def _google_vision(image_base64: str, context: str, lang: str) -> str:
    try:
        import base64

        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SCREEN_GUIDE_PROMPTS[lang],
        )

        ctx_msg = {
            "hi": f"उपयोगकर्ता यह कर रहा है: {context}\nस्क्रीन देखकर अगला कदम बताएँ।",
            "en": f"User is trying to: {context}\nLook at the screen and tell the next step.",
        }

        image_data = base64.b64decode(image_base64)
        resp = model.generate_content(
            [ctx_msg[lang], {"mime_type": "image/jpeg", "data": image_data}]
        )
        return resp.text.strip()

    except Exception as e:
        log.error("gemini_vision_error", error=str(e))
        return _vision_fallback(lang)


# ═════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════

def is_guided_flow(response: str) -> bool:
    """Check if the response involves multi-step guidance."""
    text_lower = response.lower()
    return sum(1 for kw in GUIDED_KEYWORDS if kw.lower() in text_lower) >= 2


def _fallback(user_message: str, lang: str) -> str:
    """Offline response when no API is available."""
    if lang == "hi":
        return (
            "मैं अभी सर्वर से जुड़ने में असमर्थ हूँ।\n\n"
            "कुछ उपयोगी लिंक:\n"
            "• पीएम किसान: https://pmkisan.gov.in\n"
            "• शिकायत पोर्टल: https://pgportal.gov.in\n"
            "• मुख्यमंत्री हेल्पलाइन (म.प्र.): 181\n\n"
            "कृपया कुछ देर बाद पुनः प्रयास करें।"
        )
    return (
        "I am unable to connect to the server right now.\n\n"
        "Some useful links:\n"
        "• PM Kisan: https://pmkisan.gov.in\n"
        "• Grievance Portal: https://pgportal.gov.in\n"
        "• CM Helpline (MP): 181\n\n"
        "Please try again after some time."
    )


def _vision_fallback(lang: str) -> str:
    if lang == "hi":
        return "स्क्रीन विश्लेषण में समस्या हुई। कृपया दोबारा प्रयास करें।"
    return "Screen analysis failed. Please try again."
