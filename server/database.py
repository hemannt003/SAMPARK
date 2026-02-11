"""
Async SQLAlchemy database setup, session management, and ORM models.

Models
------
- User           — optional authenticated user (Aadhaar / OAuth)
- QueryLog       — every user query + AI response (for analytics & context)
- SchemeBookmark — schemes a user has bookmarked / applied for
"""

from __future__ import annotations

import datetime as dt
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from server.config import get_settings

settings = get_settings()

# ── Engine & session factory ────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Base ────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Models ──────────────────────────────────────────────────────

class User(Base):
    """Optional user account — for personalised scheme tracking."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(15), unique=True, nullable=True, index=True)
    name = Column(String(120), nullable=True)
    state = Column(String(60), default="Madhya Pradesh")
    district = Column(String(60), nullable=True)
    category = Column(String(30), nullable=True)  # farmer / student / woman
    lang = Column(String(5), default="hi")
    hashed_password = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    queries = relationship("QueryLog", back_populates="user", lazy="selectin")
    bookmarks = relationship("SchemeBookmark", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone}>"


class QueryLog(Base):
    """Every interaction — enables conversation context and analytics."""

    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), index=True)
    lang = Column(String(5), default="hi")
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    category = Column(String(30), nullable=True)  # detected category
    is_screen_guided = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="queries")

    def __repr__(self) -> str:
        return f"<QueryLog id={self.id} query={self.user_query[:40]}>"


class SchemeBookmark(Base):
    """Schemes the user has saved or applied to."""

    __tablename__ = "scheme_bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheme_id = Column(String(60), nullable=False)
    scheme_name = Column(String(200), nullable=False)
    status = Column(String(30), default="saved")  # saved / applied / approved / rejected
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="bookmarks")

    def __repr__(self) -> str:
        return f"<SchemeBookmark scheme={self.scheme_id} status={self.status}>"


# ── Table creation ──────────────────────────────────────────────

async def create_tables() -> None:
    """Create all tables if they don't exist (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables (dev only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
