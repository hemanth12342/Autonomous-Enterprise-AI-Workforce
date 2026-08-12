"""
Project and related models.
"""
import uuid
from typing import Optional, List, Any
from sqlalchemy import String, Boolean, ForeignKey, Text, Enum as SAEnum, Float, JSON, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum
from datetime import datetime

from app.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ProjectPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Project(Base):
    """Top-level project — created from CEO analysis of a business objective."""
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True
    )
    priority: Mapped[ProjectPriority] = mapped_column(
        SAEnum(ProjectPriority), default=ProjectPriority.MEDIUM, nullable=False
    )

    # CEO analysis output
    strategic_goals: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    success_criteria: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    constraints: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    required_departments: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Planning
    architecture_proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    task_dag: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Task dependency graph

    # Budget & timeline
    budget_usd: Mapped[float] = mapped_column(Float, default=10.0)
    actual_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Progress
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    human_interventions: Mapped[int] = mapped_column(Integer, default=0)

    # Output
    github_repo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    deployment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    final_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Demo mode
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="project")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="project")
    deployments: Mapped[List["Deployment"]] = relationship("Deployment", back_populates="project")
