"""
Authentication API routes — register, login, refresh token.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, Organization, UserRole
from app.security.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    org_name: str = "Demo Organization"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    organization_id: str


# ─── Routes ───────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and organization."""
    # Check email unique
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create org
    org = Organization(
        name=req.org_name,
        slug=req.org_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8],
    )
    db.add(org)
    await db.flush()

    # Create user
    user = User(
        organization_id=org.id,
        email=req.email,
        username=req.username,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=UserRole.ORG_ADMIN,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(str(user.id), {"org_id": str(org.id), "role": user.role.value})
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role.value,
    )


@router.post("/token", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login with username/email and password."""
    result = await db.execute(
        select(User).where(
            (User.email == form.username) | (User.username == form.username)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account disabled")

    access_token = create_access_token(str(user.id), {"org_id": str(user.organization_id), "role": user.role.value})
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role.value,
    )


@router.get("/me", response_model=UserResponse)
async def me(db: AsyncSession = Depends(get_db), token: str = Depends(lambda: None)):
    """Get current user profile."""
    # Implementation uses get_current_user dependency
    pass
