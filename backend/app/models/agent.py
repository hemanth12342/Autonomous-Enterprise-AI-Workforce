"""
Agent models — defines AI agents, their state machine, runs, and permissions.
"""
import uuid
from typing import Optional, List, Any
from sqlalchemy import String, Boolean, ForeignKey, Text, Enum as SAEnum, Float, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

from app.database import Base


class AgentType(str, enum.Enum):
    CEO = "ceo"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    QA = "qa"
    DEVOPS = "devops"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    SUPPORT = "support"
    RESEARCH = "research"


class AgentStatus(str, enum.Enum):
    """Agent state machine states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_TOOL = "waiting_tool"
    WAITING_AGENT = "waiting_agent"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class Agent(Base):
    """AI Agent entity — one per agent type per organization."""
    __tablename__ = "agents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    agent_type: Mapped[AgentType] = mapped_column(SAEnum(AgentType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        SAEnum(AgentStatus), default=AgentStatus.IDLE, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Current assignment
    current_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    current_task_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Performance metrics
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    avg_task_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # LLM Configuration
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    runs: Mapped[List["AgentRun"]] = relationship("AgentRun", back_populates="agent")
    permissions: Mapped[Optional["AgentPermission"]] = relationship(
        "AgentPermission", back_populates="agent", uselist=False
    )


class AgentRun(Base):
    """A single execution run of an agent for a task."""
    __tablename__ = "agent_runs"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String(50), default="running")
    input_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")


class AgentPermission(Base):
    """Defines what an agent can read/write/execute — RBAC for agents."""
    __tablename__ = "agent_permissions"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, unique=True
    )

    # Resource permissions (JSON lists of allowed resources)
    can_read: Mapped[Any] = mapped_column(JSON, default=list)
    can_write: Mapped[Any] = mapped_column(JSON, default=list)
    can_execute: Mapped[Any] = mapped_column(JSON, default=list)
    can_delete: Mapped[Any] = mapped_column(JSON, default=list)

    # Tool permissions
    allowed_tools: Mapped[Any] = mapped_column(JSON, default=list)
    denied_tools: Mapped[Any] = mapped_column(JSON, default=list)

    # Environment restrictions
    allowed_environments: Mapped[Any] = mapped_column(JSON, default=["development", "staging"])
    can_access_production: Mapped[bool] = mapped_column(Boolean, default=False)

    # Approval policies
    requires_approval_for: Mapped[Any] = mapped_column(JSON, default=list)
    max_cost_per_task_usd: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="permissions")
