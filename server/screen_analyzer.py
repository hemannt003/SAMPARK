"""
Screen Analyzer — handles WebSocket-based screen sharing and frame analysis.

Architecture
------------
Browser → getDisplayMedia → capture JPEG frames → WebSocket → FastAPI
→ vision AI analysis → guidance text → WebSocket back → Streamlit displays + speaks
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import structlog
from fastapi import WebSocket, WebSocketDisconnect

from server.ai_engine import analyze_screen
from server.config import get_settings
from server.voice_handler import synthesize

log = structlog.get_logger()
settings = get_settings()

# ── Session tracking ────────────────────────────────────────────

@dataclass
class ScreenSession:
    """Active screen sharing session."""
    session_id: str
    websocket: WebSocket
    lang: str = "hi"
    context: str = ""           # what user is trying to do
    last_guidance: str = ""
    frame_count: int = 0
    started_at: float = field(default_factory=time.time)
    is_active: bool = True

    @property
    def duration_seconds(self) -> float:
        return time.time() - self.started_at


# All active sessions
_active_sessions: Dict[str, ScreenSession] = {}

MAX_SESSION_DURATION = 300  # 5 minutes auto-timeout
MIN_FRAME_INTERVAL = 5     # Don't analyze frames faster than 5s apart


async def handle_screen_ws(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket handler for screen sharing.

    Client sends JSON messages:
    - {"type": "start", "lang": "hi", "context": "Apply for PM-KISAN"}
    - {"type": "frame", "image": "<base64 JPEG>"}
    - {"type": "command", "action": "next|repeat|stop"}
    - {"type": "stop"}

    Server responds:
    - {"type": "guidance", "text": "...", "audio_b64": "...", "frame_num": N}
    - {"type": "status", "message": "..."}
    - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    log.info("screen_ws_connected", session_id=session_id)

    session = ScreenSession(session_id=session_id, websocket=websocket)
    _active_sessions[session_id] = session

    last_analysis_time = 0.0

    try:
        while session.is_active:
            # Check timeout
            if session.duration_seconds > MAX_SESSION_DURATION:
                await _send(websocket, {
                    "type": "status",
                    "message": "Session timed out (5 minutes). Stopping.",
                })
                break

            # Receive message
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except asyncio.TimeoutError:
                # Send heartbeat
                await _send(websocket, {"type": "status", "message": "heartbeat"})
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            # ── Start ───────────────────────────────────────────
            if msg_type == "start":
                session.lang = msg.get("lang", "hi")
                session.context = msg.get("context", "")
                await _send(websocket, {
                    "type": "status",
                    "message": "Screen sharing started. Send frames.",
                })

            # ── Frame ───────────────────────────────────────────
            elif msg_type == "frame":
                now = time.time()
                if now - last_analysis_time < MIN_FRAME_INTERVAL:
                    continue  # Skip too-frequent frames

                image_b64 = msg.get("image", "")
                if not image_b64:
                    continue

                session.frame_count += 1
                last_analysis_time = now

                # Analyze in background to not block the WebSocket
                guidance = analyze_screen(
                    image_b64, session.context, session.lang
                )

                # Don't repeat identical guidance
                if guidance and guidance != session.last_guidance:
                    session.last_guidance = guidance

                    # Generate TTS audio
                    audio_bytes = await synthesize(guidance, session.lang)
                    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

                    await _send(websocket, {
                        "type": "guidance",
                        "text": guidance,
                        "audio_b64": audio_b64,
                        "frame_num": session.frame_count,
                    })

            # ── Voice command ───────────────────────────────────
            elif msg_type == "command":
                action = msg.get("action", "")

                if action == "repeat" and session.last_guidance:
                    audio_bytes = await synthesize(
                        session.last_guidance, session.lang
                    )
                    audio_b64 = (
                        base64.b64encode(audio_bytes).decode() if audio_bytes else ""
                    )
                    await _send(websocket, {
                        "type": "guidance",
                        "text": session.last_guidance,
                        "audio_b64": audio_b64,
                        "frame_num": session.frame_count,
                    })

                elif action == "stop":
                    session.is_active = False
                    await _send(websocket, {
                        "type": "status",
                        "message": "Screen sharing stopped.",
                    })

                elif action == "next":
                    await _send(websocket, {
                        "type": "status",
                        "message": "Send next frame for analysis.",
                    })

            # ── Stop ────────────────────────────────────────────
            elif msg_type == "stop":
                session.is_active = False
                await _send(websocket, {
                    "type": "status",
                    "message": "Screen sharing stopped.",
                })

    except WebSocketDisconnect:
        log.info("screen_ws_disconnected", session_id=session_id)
    except Exception as e:
        log.error("screen_ws_error", session_id=session_id, error=str(e))
    finally:
        _active_sessions.pop(session_id, None)
        log.info(
            "screen_session_ended",
            session_id=session_id,
            frames=session.frame_count,
            duration=round(session.duration_seconds, 1),
        )


async def _send(ws: WebSocket, data: dict) -> None:
    """Send JSON message, swallowing errors if connection is dead."""
    try:
        await ws.send_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


def get_active_sessions_count() -> int:
    """Return number of active screen sharing sessions."""
    return len(_active_sessions)
