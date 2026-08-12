"""
Human approval model — human-in-the-loop gating system.
"""
import uuid
from typing import Optional, Any
from sqlalchemy import String, ForeignKey, Text, Enum as SAEnum, JSON, Boolean, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum
from datetime import datetime

from app.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ApprovalRisk(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Approval(Base):
    """Human approval request — created before high-risk operations."""
    __tablename__ = "approvals"

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    requesting_agent: Mapped[str] = mapped_column(String(100), nullable=False)

    # What is being approved
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    action_details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Risk assessment
    risk_level: Mapped[ApprovalRisk] = mapped_column(
        SAEnum(ApprovalRisk), default=ApprovalRisk.MEDIUM, nullable=False
    )
    risk_factors: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Summary for human review
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    files_changed: Mapped[Optional[int]] = mapped_column(nullable=True)
    tests_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    security_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True
    )
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="approvals")
    reviewer: Mapped[Optional["User"]] = relationship("User", back_populates="approvals")
