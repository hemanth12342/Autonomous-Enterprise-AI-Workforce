"""
Cost and token usage tracking models.
"""
import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base


class TokenUsage(Base):
    """Fine-grained token usage per LLM call."""
    __tablename__ = "token_usage"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Model info
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Token counts
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Cost
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Classification
    call_purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "code_generation"


class CostRecord(Base):
    """Aggregated cost summary per project/agent/day."""
    __tablename__ = "cost_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    period_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD

    # Totals
    total_llm_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_tool_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_llm_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
