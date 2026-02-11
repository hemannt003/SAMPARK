"""
Sampark AI — FastAPI Backend

Run:
    uvicorn main:app --reload --port 8000

Endpoints
---------
POST /api/voice/transcribe   — audio → text (Bhashini/Whisper)
POST /api/voice/synthesize   — text → audio (Bhashini/gTTS)
POST /api/chat/query         — text query → AI response + TTS
POST /api/screen/analyze     — screenshot → guidance text + TTS
GET  /api/schemes/search     — semantic search over scheme corpus
GET  /api/schemes/{category} — get schemes by category
POST /api/auth/register      — register user (optional)
POST /api/auth/login         — login → JWT (optional)
GET  /api/health             — health check
WS   /ws/screen/{session_id} — WebSocket for live screen guidance
"""

from __future__ import annotations

import base64
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

import structlog
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.ai_engine import (
    analyze_screen,
    build_rag_index,
    is_guided_flow,
    process_query,
    search_schemes,
)
from server.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_user,
    verify_password,
)
from server.config import get_settings
from server.database import (
    QueryLog,
    SchemeBookmark,
    User,
    async_session,
    create_tables,
    get_db,
)
from server.screen_analyzer import get_active_sessions_count, handle_screen_ws
from server.voice_handler import synthesize, transcribe

log = structlog.get_logger()
settings = get_settings()


# ═════════════════════════════════════════════════════════════════
#  Lifespan — startup / shutdown
# ═════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, build RAG index. Shutdown: cleanup."""
    log.info("startup", provider=settings.ai_provider)
    await create_tables()

    # Build RAG index in background (non-blocking)
    if settings.enable_rag:
        try:
            build_rag_index()
        except Exception as e:
            log.warning("rag_index_build_skipped", error=str(e))

    yield  # App runs here

    log.info("shutdown")


# ═════════════════════════════════════════════════════════════════
#  App
# ═════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Sampark AI",
    description="Voice-first government scheme assistant for rural India",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═════════════════════════════════════════════════════════════════
#  Request / Response schemas
# ═════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    lang: str = "hi"
    session_id: str = ""
    history: Optional[List[dict]] = None

class ChatResponse(BaseModel):
    reply: str
    audio_b64: str = ""
    is_guided: bool = False
    session_id: str = ""

class ScreenAnalyzeRequest(BaseModel):
    image_b64: str
    context: str = ""
    lang: str = "hi"

class ScreenAnalyzeResponse(BaseModel):
    guidance: str
    audio_b64: str = ""

class SynthesizeRequest(BaseModel):
    text: str
    lang: str = "hi"

class SchemeSearchRequest(BaseModel):
    query: str
    k: int = 3

class RegisterRequest(BaseModel):
    phone: str
    name: str = ""
    password: str = ""
    state: str = "Madhya Pradesh"
    district: str = ""
    category: str = ""
    lang: str = "hi"

class LoginRequest(BaseModel):
    phone: str
    password: str


# ═════════════════════════════════════════════════════════════════
#  Health check
# ═════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "provider": settings.ai_provider,
        "rag_enabled": settings.enable_rag,
        "screen_guide_enabled": settings.enable_screen_guide,
        "active_screen_sessions": get_active_sessions_count(),
    }


# ═════════════════════════════════════════════════════════════════
#  Voice endpoints
# ═════════════════════════════════════════════════════════════════

@app.post("/api/voice/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    lang: str = Form("hi"),
):
    """Transcribe uploaded audio file to text."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    ext = (audio.filename or "audio.webm").rsplit(".", 1)[-1]
    transcript, detected_lang = await transcribe(audio_bytes, lang, ext)

    return {
        "transcript": transcript,
        "detected_lang": detected_lang,
    }


@app.post("/api/voice/synthesize")
async def voice_synthesize(req: SynthesizeRequest):
    """Convert text to speech, return base64 MP3."""
    audio_bytes = await synthesize(req.text, req.lang)
    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""
    return {"audio_b64": audio_b64, "format": "mp3"}


# ═════════════════════════════════════════════════════════════════
#  Chat endpoint
# ═════════════════════════════════════════════════════════════════

@app.post("/api/chat/query", response_model=ChatResponse)
async def chat_query(
    req: ChatRequest,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a text query through the AI engine."""
    session_id = req.session_id or str(uuid.uuid4())[:12]

    reply = process_query(
        user_message=req.message,
        history=req.history or [],
        lang=req.lang,
        session_id=session_id,
    )

    # Generate TTS
    audio_bytes = await synthesize(reply, req.lang)
    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

    guided = is_guided_flow(reply)

    # Log to DB
    try:
        log_entry = QueryLog(
            user_id=user.id if user else None,
            session_id=session_id,
            lang=req.lang,
            user_query=req.message,
            ai_response=reply,
            is_screen_guided=guided,
        )
        db.add(log_entry)
        await db.commit()
    except Exception as e:
        log.warning("db_log_failed", error=str(e))

    return ChatResponse(
        reply=reply,
        audio_b64=audio_b64,
        is_guided=guided,
        session_id=session_id,
    )


# ═════════════════════════════════════════════════════════════════
#  Screen analysis endpoint (single-frame, non-WS)
# ═════════════════════════════════════════════════════════════════

@app.post("/api/screen/analyze", response_model=ScreenAnalyzeResponse)
async def screen_analyze(req: ScreenAnalyzeRequest):
    """Analyse a single screenshot and return guidance."""
    if not settings.enable_screen_guide:
        raise HTTPException(status_code=403, detail="Screen guide disabled")

    guidance = analyze_screen(req.image_b64, req.context, req.lang)
    audio_bytes = await synthesize(guidance, req.lang)
    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

    return ScreenAnalyzeResponse(guidance=guidance, audio_b64=audio_b64)


# ═════════════════════════════════════════════════════════════════
#  WebSocket — live screen guidance
# ═════════════════════════════════════════════════════════════════

@app.websocket("/ws/screen/{session_id}")
async def screen_ws(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time screen-guided assistance."""
    if not settings.enable_screen_guide:
        await websocket.close(code=4003, reason="Screen guide disabled")
        return
    await handle_screen_ws(websocket, session_id)


# ═════════════════════════════════════════════════════════════════
#  Scheme search
# ═════════════════════════════════════════════════════════════════

@app.get("/api/schemes/search")
async def schemes_search(query: str, k: int = 3):
    """Semantic search across scheme data."""
    results = search_schemes(query, k=k)
    return {"query": query, "results": results}


# ═════════════════════════════════════════════════════════════════
#  Auth endpoints (optional)
# ═════════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user (optional auth)."""
    if not settings.enable_auth:
        raise HTTPException(status_code=403, detail="Auth disabled")

    existing = await db.execute(select(User).where(User.phone == req.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone already registered")

    user = User(
        phone=req.phone,
        name=req.name,
        state=req.state,
        district=req.district,
        category=req.category,
        lang=req.lang,
        hashed_password=hash_password(req.password) if req.password else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.phone)
    return {"user_id": user.id, "token": token}


@app.post("/api/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT."""
    if not settings.enable_auth:
        raise HTTPException(status_code=403, detail="Auth disabled")

    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id, user.phone)
    return {"user_id": user.id, "token": token}


# ═════════════════════════════════════════════════════════════════
#  Run directly
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=True,
    )
