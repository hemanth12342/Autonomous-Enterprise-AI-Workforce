"""
Inter-agent message model — the communication bus.
"""
import uuid
from typing import Optional, Any
from sqlalchemy import String, ForeignKey, Text, Enum as SAEnum, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

from app.database import Base


class MessageType(str, enum.Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESULT = "review_result"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    ESCALATION = "escalation"
    STATUS_UPDATE = "status_update"
    INFORMATION_REQUEST = "information_request"
    INFORMATION_RESPONSE = "information_response"


class MessagePriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Message(Base):
    """Structured inter-agent message — the communication backbone."""
    __tablename__ = "messages"

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    # Routing
    sender: Mapped[str] = mapped_column(String(100), nullable=False)  # agent type or "human"
    receiver: Mapped[str] = mapped_column(String(100), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(SAEnum(MessageType), nullable=False)
    priority: Mapped[MessagePriority] = mapped_column(
        SAEnum(MessagePriority), default=MessagePriority.MEDIUM
    )

    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Flags
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="messages")
