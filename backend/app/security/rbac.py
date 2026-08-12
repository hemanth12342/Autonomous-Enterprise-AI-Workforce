"""
RBAC — Role-Based Access Control for users.
"""
from functools import wraps
from fastapi import HTTPException, status
from app.models.user import User, UserRole


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.DEVELOPER: 1,
    UserRole.MANAGER: 2,
    UserRole.ORG_ADMIN: 3,
    UserRole.SUPER_ADMIN: 4,
}

# Maps action → minimum role required
ACTION_PERMISSIONS: dict[str, UserRole] = {
    # Projects
    "project:read":    UserRole.VIEWER,
    "project:create":  UserRole.DEVELOPER,
    "project:update":  UserRole.MANAGER,
    "project:delete":  UserRole.ORG_ADMIN,
    "project:start":   UserRole.DEVELOPER,
    # Tasks
    "task:read":       UserRole.VIEWER,
    "task:approve":    UserRole.MANAGER,
    "task:reject":     UserRole.MANAGER,
    # Approvals
    "approval:read":   UserRole.VIEWER,
    "approval:approve": UserRole.MANAGER,
    "approval:reject":  UserRole.MANAGER,
    # Agents
    "agent:read":      UserRole.VIEWER,
    "agent:execute":   UserRole.DEVELOPER,
    # Audit
    "audit:read":      UserRole.MANAGER,
    # Costs
    "cost:read":       UserRole.MANAGER,
    # Settings
    "settings:read":   UserRole.ORG_ADMIN,
    "settings:write":  UserRole.ORG_ADMIN,
    # Documents
    "document:read":   UserRole.VIEWER,
    "document:create": UserRole.DEVELOPER,
    "document:delete": UserRole.MANAGER,
}


def has_permission(user: User, action: str) -> bool:
    """Check if a user has the required role for an action."""
    required_role = ACTION_PERMISSIONS.get(action)
    if required_role is None:
        return False
    user_level = ROLE_HIERARCHY.get(user.role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 99)
    return user_level >= required_level


def require_permission(action: str):
    """FastAPI dependency factory — raises 403 if user lacks permission."""
    from fastapi import Depends
    from app.security.auth import get_current_user

    async def check(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {action}",
            )
        return user

    return check


def require_role(minimum_role: UserRole):
    """FastAPI dependency factory — requires a minimum role level."""
    from fastapi import Depends
    from app.security.auth import get_current_user

    async def check(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 99)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires minimum role: {minimum_role.value}",
            )
        return user

    return check
