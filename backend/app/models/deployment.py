"""
Deployment and Incident models.
"""
import uuid
from typing import Optional, Any, List
from sqlalchemy import String, ForeignKey, Text, Enum as SAEnum, JSON, Boolean, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum
from datetime import datetime

from app.database import Base


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Deployment(Base):
    """Deployment record — tracks every production/staging deployment."""
    __tablename__ = "deployments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    approval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    version: Mapped[str] = mapped_column(String(50), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="production")
    status: Mapped[DeploymentStatus] = mapped_column(
        SAEnum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False, index=True
    )

    # Build details
    docker_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    docker_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    git_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Deployment target
    deployment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    kubernetes_namespace: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Health
    health_check_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    health_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    smoke_tests_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Metrics
    deployment_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cost
    estimated_monthly_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Logs/events
    deployment_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deployment_events: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="deployments")
    incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="deployment")


class Incident(Base):
    """Production incident — detected by DevOps agent monitoring."""
    __tablename__ = "incidents"

    deployment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity), nullable=False
    )

    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_to_resolution_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    error_rate_at_detection: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recovery_actions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    required_human_intervention: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    deployment: Mapped["Deployment"] = relationship("Deployment", back_populates="incidents")
