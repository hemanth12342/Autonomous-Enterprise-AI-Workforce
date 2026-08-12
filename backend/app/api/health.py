"""
Health check API endpoint.
"""
from fastapi import APIRouter
from app.config import settings
from app.database import engine
from app.memory.short_term import get_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """System health check — checks all critical dependencies."""
    checks = {}

    # PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception as e:
        checks["postgres"] = f"unhealthy: {str(e)[:50]}"

    # Redis
    try:
        redis = get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)[:50]}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode,
        "llm_provider": settings.llm_provider,
        "checks": checks,
    }
