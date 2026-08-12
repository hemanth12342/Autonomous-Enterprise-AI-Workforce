"""Audit Log API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.security.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    limit: int = 100,
    actor: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List audit logs for the organization."""
    query = select(AuditLog).where(
        AuditLog.organization_id == current_user.organization_id
    ).order_by(AuditLog.created_at.desc()).limit(limit)
    if actor:
        query = query.where(AuditLog.actor == actor)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "actor": l.actor,
            "actor_type": l.actor_type,
            "action": l.action,
            "resource_type": l.resource_type,
            "result": l.result,
            "severity": l.severity,
            "tool": l.tool,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
