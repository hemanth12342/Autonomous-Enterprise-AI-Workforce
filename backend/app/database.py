"""
Database engine, session factory, and base model.
Uses SQLAlchemy async with asyncpg driver.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.config import settings


# ─── Build asyncpg-compatible URL ─────────────────────────────────────────────
def _build_engine_args(raw_url: str):
    """
    asyncpg does NOT support ?sslmode= or ?channel_binding= query params.
    Strip those params and pass ssl=True via connect_args instead.
    """
    parsed = urlparse(raw_url)
    params = parse_qs(parsed.query)

    # Detect if SSL was requested via the query string
    needs_ssl = params.pop("sslmode", [""])[0] in ("require", "verify-ca", "verify-full")
    params.pop("channel_binding", None)  # also unsupported by asyncpg

    # Rebuild the URL without the stripped params
    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args = {}
    if needs_ssl:
        connect_args["ssl"] = True

    return clean_url, connect_args


_db_url, _connect_args = _build_engine_args(settings.database_url)

# ─── Async Engine ─────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    _db_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

# ─── Session Factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─── Base Model ───────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base ORM class — all models inherit this."""

    id: MappedColumn[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: MappedColumn[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: MappedColumn[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ─── Dependency ───────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for injecting async DB sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for DB sessions outside FastAPI requests (workers, scripts)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Init DB ──────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables and enable pgvector extension."""
    # IMPORTANT: Import all models here so Base.metadata knows about every table
    # before create_all is called. Without this, no tables are created.
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        # Enable pgvector extension (may fail if not available — that's ok)
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        except Exception:
            pass
        # Create all tables registered in Base.metadata
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose engine connections on shutdown."""
    await engine.dispose()
