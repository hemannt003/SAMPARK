# Sampark AI — Voice-First Government Scheme Assistant

> **सरकारी योजनाओं की जानकारी — बस बोलिए!**
> Government scheme information — just speak!

A production-grade, voice-first web application that helps farmers, students, and women in rural India access government schemes, file grievances, and navigate official websites — all through simple voice commands in Hindi or English.

**Special focus: Madhya Pradesh schemes** (Ladli Bahna, Mukhyamantri Kisan Kalyan, Medhavi Vidyarthi, CM Helpline 181).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER (Mobile/Desktop)                     │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │  Mic Button   │  │ Text Input   │  │  Screen Share           │    │
│  │ (JS Component)│  │ (Streamlit)  │  │  (getDisplayMedia JS)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────┘    │
│         │ audio b64        │ text                 │ JPEG frames     │
└─────────┼──────────────────┼──────────────────────┼─────────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND (app.py)                       │
│  • WhatsApp-style chat  • Hindi/English toggle  • PWA support       │
│  • Audio playback       • Screen guide UI       • gTTS fallback     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (main.py)                        │
│                                                                     │
│  POST /api/voice/transcribe  ──→  Bhashini STT → Whisper fallback  │
│  POST /api/voice/synthesize  ──→  Bhashini TTS → gTTS fallback     │
│  POST /api/chat/query        ──→  AI Engine + RAG                   │
│  POST /api/screen/analyze    ──→  Vision AI (GPT-4o/Grok/Gemini)   │
│  WS   /ws/screen/{session}   ──→  Real-time screen guidance         │
│  GET  /api/schemes/search    ──→  FAISS semantic search             │
│  POST /api/auth/*            ──→  JWT auth (optional)               │
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │ AI Engine   │  │   RAG      │  │  Voice     │  │  Screen      │ │
│  │ xAI/OpenAI/ │  │  FAISS +   │  │  Bhashini  │  │  Analyzer    │ │
│  │ Gemini      │  │  LangChain │  │  + Whisper  │  │  (Vision AI) │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SQLite/PostgreSQL — Users, Query Logs, Scheme Bookmarks       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Core
- **Voice-first UI** — large mic button, tap and speak in Hindi or English
- **AI-powered responses** — understands queries about schemes, eligibility, complaints
- **Audio responses** — every answer is spoken aloud (Hindi-preferred)
- **WhatsApp-style chat** — scrollable history with audio playback
- **Language toggle** — pure Hindi (Devanagari) or pure English, no Hinglish

### Screen-Guided Assistance
- After multi-step answers, the app offers: *"Shall I guide you by seeing your screen?"*
- Uses `getDisplayMedia` API to capture the user's screen
- AI vision model (GPT-4o / Grok Vision / Gemini) analyzes screenshots
- Speaks guidance like: *"Press the green 'Apply Now' button on the top-right"*
- WebSocket support for real-time low-latency guidance
- Auto-timeout after 5 minutes, encrypted streams

### AI & Data
- **Multi-provider**: xAI Grok (primary), OpenAI GPT-4o, Google Gemini
- **RAG**: FAISS vector store with 9+ scheme documents for semantic search
- **Bhashini API**: Indian govt STT/TTS supporting 22+ languages
- **Fallback chain**: Bhashini → Whisper → Web Speech API (offline)
- **Ethical AI**: Always cites sources, adds disclaimers, no legal advice

### Infrastructure
- **FastAPI + Streamlit** hybrid architecture
- **Docker** containerized with `docker-compose.yml`
- **SQLite** (dev) / **PostgreSQL** (prod) via async SQLAlchemy
- **PWA** installable on mobile with offline shell caching
- **JWT auth** (optional) for personalized tracking
- **Structured logging** via structlog

---

## Quick Start

### Prerequisites
- Python 3.11+
- At least one API key: OpenAI, xAI (Grok), or Google Gemini

### 1. Clone and setup

```bash
git clone https://github.com/hemannt003/SAMPARK.git
cd SAMPARK
cp .env.example .env
# Edit .env with your API key(s)
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run (development)

```bash
# Option A: Both servers at once
chmod +x scripts/run.sh
./scripts/run.sh

# Option B: Separately
uvicorn main:app --reload --port 8000   # Terminal 1
streamlit run app.py                     # Terminal 2
```

### 4. Open in browser

- **App**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Docker

```bash
docker-compose up --build
# App: http://localhost:8501
# API: http://localhost:8000
```

---

## Project Structure

```
SAMPARK/
├── app.py                    # Streamlit frontend (v2)
├── main.py                   # FastAPI backend
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image
├── docker-compose.yml        # Multi-service orchestration
├── .env.example              # Environment variable template
├── pytest.ini                # Test configuration
│
├── server/                   # FastAPI backend modules
│   ├── config.py             # Pydantic settings management
│   ├── database.py           # SQLAlchemy models + async DB
│   ├── ai_engine.py          # Multi-provider AI + RAG + vision
│   ├── voice_handler.py      # Bhashini/Whisper STT + TTS
│   ├── screen_analyzer.py    # WebSocket screen guidance
│   └── auth.py               # JWT authentication
│
├── utils/                    # Streamlit-specific utilities
│   ├── i18n.py               # Hindi/English translations
│   ├── voice.py              # Local STT/TTS (fallback)
│   └── ai_engine.py          # Local AI (fallback)
│
├── st_components/            # Streamlit custom JS components
│   ├── styles.py             # Custom CSS injection
│   ├── audio_recorder/       # Big mic button component
│   │   └── index.html
│   └── screen_share/         # getDisplayMedia component
│       └── index.html
│
├── data/
│   ├── schemes.json          # Scheme corpus (MP + national)
│   └── faiss_index/          # FAISS vector store (auto-built)
│
├── static/
│   ├── manifest.json         # PWA manifest
│   └── sw.js                 # Service worker
│
├── tests/                    # pytest test suite
│   ├── test_ai.py
│   └── test_api.py
│
├── scripts/
│   └── run.sh                # Dev startup script
│
├── frontend/                 # React app (legacy/alternative)
├── backend/                  # AWS Lambda backend (legacy)
└── infrastructure/           # AWS SAM deployment
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice/transcribe` | Audio file → text (Bhashini/Whisper) |
| `POST` | `/api/voice/synthesize` | Text → audio MP3 (Bhashini/gTTS) |
| `POST` | `/api/chat/query` | Text query → AI response + TTS |
| `POST` | `/api/screen/analyze` | Screenshot → guidance + TTS |
| `GET` | `/api/schemes/search` | Semantic search over schemes |
| `WS` | `/ws/screen/{session_id}` | Live screen guidance |
| `POST` | `/api/auth/register` | Register user (optional) |
| `POST` | `/api/auth/login` | Login → JWT (optional) |
| `GET` | `/api/health` | Health check |

---

## Schemes Database

| Category | Scheme | State |
|----------|--------|-------|
| Farmer | PM Kisan Samman Nidhi | All India |
| Farmer | Kisan Credit Card | All India |
| Farmer | Mukhyamantri Kisan Kalyan Yojana | Madhya Pradesh |
| Woman | Ladli Bahna Yojana | Madhya Pradesh |
| Woman | PM Ujjwala Yojana | All India |
| Student | PM Vidyalakshmi Yojana | All India |
| Student | Mukhyamantri Medhavi Vidyarthi Yojana | Madhya Pradesh |
| Grievance | CPGRAMS (PG Portal) | All India |
| Grievance | CM Helpline 181 | Madhya Pradesh |

---

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_PROVIDER` | Yes | `openai`, `xai`, or `google` |
| `OPENAI_API_KEY` | If provider=openai | GPT-4o for text + vision |
| `XAI_API_KEY` | If provider=xai | Grok for text + vision |
| `BHASHINI_API_KEY` | Optional | Indian govt STT/TTS (22+ languages) |
| `DATABASE_URL` | Optional | Default: SQLite `./sampark.db` |

---

## Privacy & Compliance

- **DPDP Act (India)**: No personal data stored without consent
- **Screen sharing**: Explicit user consent required; auto-timeout at 5 min
- **Auth**: Optional; anonymous usage supported
- **Logging**: Anonymized query logs only; no audio stored
- **Disclaimer**: All responses include "This is for guidance only"

---

## Testing

```bash
pytest                    # Run all tests
pytest tests/test_ai.py   # AI engine tests only
pytest tests/test_api.py  # API endpoint tests only
```

---

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| v1.0 | Voice-first Streamlit MVP | Done |
| v2.0 | FastAPI backend + RAG + Screen guide + Docker | Done |
| v2.1 | Bhashini integration for 22+ languages | Ready |
| v2.2 | Redis caching for AI responses | Planned |
| v2.3 | Twilio SMS/WhatsApp notifications | Planned |
| v3.0 | React Native mobile app | Planned |
| v3.1 | Playwright headless browser for auto form-fill | Planned |
| v3.2 | ML-based intent detection (fine-tuned model) | Planned |
| v3.3 | Direct govt API integrations (PM-KISAN status check) | Planned |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "feat: Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — Free for educational and non-commercial use.

---

**Made with care for Bharat** 🇮🇳
