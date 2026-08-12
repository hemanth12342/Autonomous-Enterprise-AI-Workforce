"""
User and Organization models — multi-tenant foundation.
"""
import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class Organization(Base):
    """Multi-tenant organization (tenant root)."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_agents: Mapped[int] = mapped_column(default=10)
    max_projects: Mapped[int] = mapped_column(default=50)
    monthly_budget_usd: Mapped[float] = mapped_column(default=100.0)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="organization")


class User(Base):
    """Platform user — belongs to an organization."""
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.DEVELOPER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="reviewer")
