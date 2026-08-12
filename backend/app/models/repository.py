"""
Repository and Pull Request models — GitHub integration.
"""
import uuid
from typing import Optional, Any
from sqlalchemy import String, ForeignKey, Text, Enum as SAEnum, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

from app.database import Base


class PRStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


class Repository(Base):
    """GitHub repository linked to a project."""
    __tablename__ = "repositories"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )

    github_repo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class PullRequest(Base):
    """Pull request created by the Developer agent."""
    __tablename__ = "pull_requests"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    github_pr_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), default="main")
    pr_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[PRStatus] = mapped_column(
        SAEnum(PRStatus), default=PRStatus.OPEN, nullable=False
    )

    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)

    qa_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    security_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    human_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    qa_report: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    security_report: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    merged_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
