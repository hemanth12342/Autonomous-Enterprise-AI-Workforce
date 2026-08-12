"""Tasks API and Metrics API stubs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.security.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_tasks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Task).order_by(Task.created_at.desc()).limit(100))
    tasks = result.scalars().all()
    return [{"id": str(t.id), "title": t.title, "status": t.status.value, "assigned_agent_type": t.assigned_agent_type} for t in tasks]


@router.post("/{task_id}/approve")
async def approve_task(task_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = TaskStatus.COMPLETED
    return {"message": "Task approved"}


@router.post("/{task_id}/reject")
async def reject_task(task_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = TaskStatus.CANCELLED
    return {"message": "Task rejected"}
