"""
AI Engine — supports OpenAI (GPT-4o), xAI (Grok), Google Gemini.
Handles both text queries and multimodal (vision) screen analysis.
"""

import os
import json
from utils.i18n import SYSTEM_PROMPT, SCREEN_GUIDE_PROMPT, MULTI_STEP_KEYWORDS


# ─────────────────────────────────────────────────────────────────
# Client factory
# ─────────────────────────────────────────────────────────────────

def _get_provider():
    return os.getenv("AI_PROVIDER", "openai").lower()


def _get_openai_client():
    from openai import OpenAI

    provider = _get_provider()
    if provider == "xai":
        return OpenAI(
            api_key=os.getenv("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1",
        )
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _get_model_name(vision: bool = False):
    provider = _get_provider()
    if provider == "xai":
        return "grok-2-vision-1212" if vision else "grok-2-1212"
    if provider == "google":
        return "gemini-1.5-flash"
    # openai
    return "gpt-4o"


# ─────────────────────────────────────────────────────────────────
# Text query processing
# ─────────────────────────────────────────────────────────────────

def get_ai_response(
    user_message: str,
    chat_history: list,
    lang: str = "hi",
) -> str:
    """
    Process a text query through the AI.
    chat_history: list of {"role": "user"/"assistant", "content": str}
    Returns the assistant's reply as a string.
    """
    provider = _get_provider()

    if provider == "google":
        return _google_text(user_message, chat_history, lang)

    # OpenAI-compatible path (works for openai and xai)
    return _openai_text(user_message, chat_history, lang)


def _openai_text(user_message, chat_history, lang):
    try:
        client = _get_openai_client()
        messages = [{"role": "system", "content": SYSTEM_PROMPT[lang]}]

        # Add recent history (last 10 turns to fit context)
        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=_get_model_name(vision=False),
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[AI Text Error] {e}")
        return _fallback_response(user_message, lang)


def _google_text(user_message, chat_history, lang):
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel(
            model_name=_get_model_name(),
            system_instruction=SYSTEM_PROMPT[lang],
        )

        # Build conversation
        history_text = ""
        for msg in chat_history[-10:]:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{prefix}: {msg['content']}\n"

        prompt = f"{history_text}User: {user_message}\nAssistant:"
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"[Gemini Text Error] {e}")
        return _fallback_response(user_message, lang)


# ─────────────────────────────────────────────────────────────────
# Screen analysis (multimodal / vision)
# ─────────────────────────────────────────────────────────────────

def analyze_screen_capture(
    image_base64: str,
    guide_context: str,
    lang: str = "hi",
) -> str:
    """
    Analyze a screenshot and return step-by-step guidance.
    image_base64: JPEG image as base64 string (without the data: prefix).
    guide_context: what the user is trying to do (e.g. "Apply for PM-KISAN").
    """
    provider = _get_provider()

    if provider == "google":
        return _google_vision(image_base64, guide_context, lang)

    return _openai_vision(image_base64, guide_context, lang)


def _openai_vision(image_base64, guide_context, lang):
    try:
        client = _get_openai_client()

        context_msg = {
            "hi": f"उपयोगकर्ता यह करने का प्रयास कर रहा है: {guide_context}\nकृपया स्क्रीन देखकर अगला कदम बताएँ।",
            "en": f"The user is trying to: {guide_context}\nPlease look at the screen and tell them the next step.",
        }

        messages = [
            {"role": "system", "content": SCREEN_GUIDE_PROMPT[lang]},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": context_msg[lang]},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                ],
            },
        ]

        response = client.chat.completions.create(
            model=_get_model_name(vision=True),
            messages=messages,
            max_tokens=500,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[AI Vision Error] {e}")
        if lang == "hi":
            return "स्क्रीन का विश्लेषण करने में समस्या हुई। कृपया दोबारा कोशिश करें।"
        return "There was a problem analyzing the screen. Please try again."


def _google_vision(image_base64, guide_context, lang):
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SCREEN_GUIDE_PROMPT[lang],
        )

        context_msg = {
            "hi": f"उपयोगकर्ता यह करने का प्रयास कर रहा है: {guide_context}\nकृपया स्क्रीन देखकर अगला कदम बताएँ।",
            "en": f"The user is trying to: {guide_context}\nPlease look at the screen and tell them the next step.",
        }

        image_data = base64.b64decode(image_base64)
        response = model.generate_content(
            [
                context_msg[lang],
                {"mime_type": "image/jpeg", "data": image_data},
            ]
        )
        return response.text.strip()

    except Exception as e:
        print(f"[Gemini Vision Error] {e}")
        if lang == "hi":
            return "स्क्रीन का विश्लेषण करने में समस्या हुई। कृपया दोबारा कोशिश करें।"
        return "There was a problem analyzing the screen. Please try again."


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def check_if_guided_flow(ai_response: str) -> bool:
    """
    Check whether the AI response involves a multi-step process
    that would benefit from screen-guided assistance.
    """
    text_lower = ai_response.lower()
    matches = sum(1 for kw in MULTI_STEP_KEYWORDS if kw.lower() in text_lower)
    return matches >= 2


def _fallback_response(user_message: str, lang: str) -> str:
    """
    Offline / fallback response when API is unavailable.
    """
    text_lower = user_message.lower()

    # Farmer keywords
    farmer_kw = ["किसान", "खेती", "कृषि", "farmer", "kisan", "crop", "land"]
    # Student keywords
    student_kw = ["विद्यार्थी", "छात्र", "पढ़ाई", "student", "scholarship", "education"]
    # Woman keywords
    woman_kw = ["महिला", "स्त्री", "बेटी", "woman", "women", "girl"]

    if any(kw in text_lower for kw in farmer_kw):
        if lang == "hi":
            return (
                "**पीएम किसान सम्मान निधि योजना**\n\n"
                "**पात्रता:** छोटे एवं सीमांत किसान जिनके पास 2 हेक्टेयर से कम भूमि है।\n\n"
                "**लाभ:** प्रति वर्ष ₹6,000 — तीन किस्तों में ₹2,000।\n\n"
                "**आवश्यक दस्तावेज़:**\n"
                "1. आधार कार्ड\n2. बैंक खाता पासबुक\n3. भूमि के कागज़ात\n4. मोबाइल नंबर\n\n"
                "**आवेदन के चरण:**\n"
                "1. वेबसाइट खोलें: https://pmkisan.gov.in\n"
                "2. \"New Farmer Registration\" पर क्लिक करें\n"
                "3. अपना आधार नंबर भरें\n"
                "4. बैंक खाते की जानकारी भरें\n"
                "5. भूमि की जानकारी भरें\n"
                "6. फ़ॉर्म जमा करें\n\n"
                "क्या आप चाहते हैं कि मैं आपकी स्क्रीन देखकर गाइड करूँ?"
            )
        return (
            "**PM Kisan Samman Nidhi Yojana**\n\n"
            "**Eligibility:** Small and marginal farmers with less than 2 hectares of land.\n\n"
            "**Benefit:** ₹6,000 per year — ₹2,000 in three instalments.\n\n"
            "**Documents Required:**\n"
            "1. Aadhaar Card\n2. Bank Account Passbook\n3. Land Records\n4. Mobile Number\n\n"
            "**Application Steps:**\n"
            "1. Open website: https://pmkisan.gov.in\n"
            "2. Click \"New Farmer Registration\"\n"
            "3. Enter your Aadhaar number\n"
            "4. Fill in bank account details\n"
            "5. Enter land details\n"
            "6. Submit the form\n\n"
            "Would you like me to guide you by seeing your screen?"
        )

    if any(kw in text_lower for kw in student_kw):
        if lang == "hi":
            return (
                "**पीएम विद्यालक्ष्मी योजना**\n\n"
                "**पात्रता:** उच्च शिक्षा के लिए ऋण की आवश्यकता वाले विद्यार्थी।\n\n"
                "**लाभ:** कम ब्याज दर पर शिक्षा ऋण।\n\n"
                "**आवश्यक दस्तावेज़:**\n"
                "1. आधार कार्ड\n2. प्रवेश पत्र\n3. अंकतालिका\n4. आय प्रमाण पत्र\n5. बैंक खाता\n\n"
                "**आवेदन के चरण:**\n"
                "1. वेबसाइट खोलें: https://www.vidyalakshmi.co.in\n"
                "2. \"Register\" पर क्लिक करें\n"
                "3. कॉलेज और पाठ्यक्रम चुनें\n"
                "4. ऋण राशि भरें\n"
                "5. दस्तावेज़ अपलोड करें\n"
                "6. बैंक चुनें और आवेदन करें\n\n"
                "क्या आप चाहते हैं कि मैं आपकी स्क्रीन देखकर गाइड करूँ?"
            )
        return (
            "**PM Vidyalakshmi Yojana**\n\n"
            "**Eligibility:** Students who need loans for higher education.\n\n"
            "**Benefit:** Education loan at low interest rates.\n\n"
            "**Documents Required:**\n"
            "1. Aadhaar Card\n2. Admission Letter\n3. Marksheet\n4. Income Certificate\n5. Bank Account\n\n"
            "**Application Steps:**\n"
            "1. Open website: https://www.vidyalakshmi.co.in\n"
            "2. Click \"Register\"\n"
            "3. Select college and course\n"
            "4. Enter loan amount\n"
            "5. Upload documents\n"
            "6. Select bank and apply\n\n"
            "Would you like me to guide you by seeing your screen?"
        )

    if any(kw in text_lower for kw in woman_kw):
        if lang == "hi":
            return (
                "**प्रधानमंत्री उज्ज्वला योजना**\n\n"
                "**पात्रता:** बीपीएल परिवार की 18 वर्ष से अधिक आयु की महिलाएँ।\n\n"
                "**लाभ:** निःशुल्क एलपीजी कनेक्शन, ₹1,600 की सब्सिडी।\n\n"
                "**आवश्यक दस्तावेज़:**\n"
                "1. आधार कार्ड\n2. बीपीएल राशन कार्ड\n3. बैंक खाता पासबुक\n4. पासपोर्ट साइज़ फ़ोटो\n\n"
                "**आवेदन के चरण:**\n"
                "1. नज़दीकी एलपीजी वितरक के पास जाएँ\n"
                "2. उज्ज्वला योजना का फ़ॉर्म लें\n"
                "3. फ़ॉर्म में जानकारी भरें\n"
                "4. दस्तावेज़ों की प्रति संलग्न करें\n"
                "5. केवाईसी पूर्ण करें\n\n"
                "क्या आप चाहते हैं कि मैं आपकी स्क्रीन देखकर गाइड करूँ?"
            )
        return (
            "**Pradhan Mantri Ujjwala Yojana**\n\n"
            "**Eligibility:** Women above 18 from BPL families.\n\n"
            "**Benefit:** Free LPG connection with ₹1,600 subsidy.\n\n"
            "**Documents Required:**\n"
            "1. Aadhaar Card\n2. BPL Ration Card\n3. Bank Account Passbook\n4. Passport Photo\n\n"
            "**Application Steps:**\n"
            "1. Visit nearest LPG distributor\n"
            "2. Get the Ujjwala Yojana form\n"
            "3. Fill in your details\n"
            "4. Attach document copies\n"
            "5. Complete KYC verification\n\n"
            "Would you like me to guide you by seeing your screen?"
        )

    # Generic
    if lang == "hi":
        return (
            "मैं आपकी सहायता के लिए तैयार हूँ! कृपया बताएँ:\n"
            "• आप किसान हैं, विद्यार्थी हैं, या महिला हैं?\n"
            "• आपको किस योजना या सेवा की जानकारी चाहिए?\n\n"
            "उदाहरण: \"किसानों के लिए कोई योजना बताइए\" या \"छात्रवृत्ति कैसे मिलेगी?\""
        )
    return (
        "I am ready to help! Please tell me:\n"
        "• Are you a farmer, student, or woman?\n"
        "• Which scheme or service do you need information about?\n\n"
        "Example: \"Tell me about farmer schemes\" or \"How can I get a scholarship?\""
    )
