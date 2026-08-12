"""Costs API — token usage and cost analytics."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.cost import TokenUsage, CostRecord
from app.models.user import User
from app.security.auth import get_current_user

router = APIRouter()


@router.get("/summary")
async def cost_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost summary for the organization."""
    result = await db.execute(
        select(
            func.sum(TokenUsage.cost_usd).label("total"),
            func.sum(TokenUsage.total_tokens).label("tokens"),
            func.count(TokenUsage.id).label("calls"),
        ).where(TokenUsage.organization_id == current_user.organization_id)
    )
    row = result.one_or_none()
    return {
        "total_cost_usd": float(row.total or 0),
        "total_tokens": int(row.tokens or 0),
        "total_llm_calls": int(row.calls or 0),
    }


@router.get("/by-agent")
async def costs_by_agent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost breakdown by agent type."""
    result = await db.execute(
        select(
            TokenUsage.agent_type,
            func.sum(TokenUsage.cost_usd).label("total"),
            func.sum(TokenUsage.total_tokens).label("tokens"),
        )
        .where(TokenUsage.organization_id == current_user.organization_id)
        .group_by(TokenUsage.agent_type)
    )
    return [{"agent_type": row.agent_type, "cost_usd": float(row.total or 0), "tokens": int(row.tokens or 0)} for row in result]


@router.get("/by-model")
async def costs_by_model(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost breakdown by LLM model."""
    result = await db.execute(
        select(
            TokenUsage.model_name,
            func.sum(TokenUsage.cost_usd).label("total"),
            func.sum(TokenUsage.total_tokens).label("tokens"),
        )
        .where(TokenUsage.organization_id == current_user.organization_id)
        .group_by(TokenUsage.model_name)
    )
    return [{"model": row.model_name, "cost_usd": float(row.total or 0), "tokens": int(row.tokens or 0)} for row in result]
