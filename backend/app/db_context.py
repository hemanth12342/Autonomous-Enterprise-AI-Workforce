"""Database context manager for background tasks."""
from contextlib import asynccontextmanager
from app.database import AsyncSessionLocal


@asynccontextmanager
async def get_db_context():
    """Async context manager for DB sessions in background tasks."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
