"""
Projects API — CRUD, start workflow, get activity.
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db, get_db_context
from app.models.project import Project, ProjectStatus, ProjectPriority
from app.models.task import Task, TaskDependency, TaskStatus, TaskType, TaskPriority
from app.security.auth import get_current_user
from app.models.user import User
from app.orchestration.langgraph_engine import get_workflow_engine

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────
class CreateProjectRequest(BaseModel):
    name: str
    business_objective: str
    description: Optional[str] = None
    priority: str = "medium"
    budget_usd: float = 10.0
    is_demo: bool = False


class ProjectResponse(BaseModel):
    id: str
    name: str
    business_objective: str
    status: str
    priority: str
    progress_percent: float
    total_tasks: int
    completed_tasks: int
    actual_cost_usd: float
    budget_usd: float
    deployment_url: Optional[str]
    created_at: str


# ─── Routes ───────────────────────────────────────────────────────────────────
@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    req: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    project = Project(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        name=req.name,
        business_objective=req.business_objective,
        description=req.description,
        status=ProjectStatus.DRAFT,
        priority=ProjectPriority(req.priority),
        budget_usd=req.budget_usd,
        is_demo=req.is_demo,
    )
    db.add(project)
    await db.flush()

    return _project_to_response(project)


@router.get("/")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the organization."""
    result = await db.execute(
        select(Project)
        .where(Project.organization_id == current_user.organization_id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project details with tasks."""
    project = await _get_project_or_404(project_id, current_user.organization_id, db)
    result = await db.execute(
        select(Task).where(Task.project_id == project.id).order_by(Task.sequence_order)
    )
    tasks = result.scalars().all()

    return {
        **_project_to_response(project),
        "tasks": [_task_to_dict(t) for t in tasks],
        "final_report": project.final_report,
        "task_dag": project.task_dag,
    }


@router.post("/{project_id}/start")
async def start_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start the AI Workforce workflow for a project."""
    project = await _get_project_or_404(project_id, current_user.organization_id, db)

    if project.status not in [ProjectStatus.DRAFT, ProjectStatus.FAILED]:
        raise HTTPException(status_code=400, detail=f"Project is already {project.status.value}")

    project.status = ProjectStatus.PLANNING
    project.started_at = datetime.now(timezone.utc)
    await db.flush()

    # Run workflow in background
    background_tasks.add_task(
        _run_workflow_background,
        str(project.id),
        str(project.organization_id),
        project.business_objective,
        project.is_demo,
    )

    return {"message": "AI Workforce workflow started", "project_id": project_id, "status": "planning"}


@router.get("/{project_id}/activity")
async def get_project_activity(
    project_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent activity for a project."""
    from app.models.audit import AuditLog
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.project_id == uuid.UUID(project_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [{"actor": l.actor, "action": l.action, "timestamp": l.created_at.isoformat()} for l in logs]


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all tasks for a project."""
    result = await db.execute(
        select(Task)
        .where(Task.project_id == uuid.UUID(project_id))
        .order_by(Task.sequence_order)
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


# ─── Helpers ──────────────────────────────────────────────────────────────────
async def _get_project_or_404(project_id: str, org_id: uuid.UUID, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == uuid.UUID(project_id),
            Project.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _project_to_response(p: Project) -> dict:
    total = p.total_tasks or 1
    return {
        "id": str(p.id),
        "name": p.name,
        "business_objective": p.business_objective,
        "status": p.status.value,
        "priority": p.priority.value,
        "progress_percent": round((p.completed_tasks / total) * 100, 1) if total else 0,
        "total_tasks": p.total_tasks,
        "completed_tasks": p.completed_tasks,
        "actual_cost_usd": p.actual_cost_usd,
        "budget_usd": p.budget_usd,
        "deployment_url": p.deployment_url,
        "created_at": p.created_at.isoformat(),
        "is_demo": p.is_demo,
    }


def _task_to_dict(t: Task) -> dict:
    return {
        "id": str(t.id),
        "title": t.title,
        "description": t.description,
        "task_type": t.task_type.value,
        "status": t.status.value,
        "priority": t.priority.value,
        "assigned_agent_type": t.assigned_agent_type,
        "sequence_order": t.sequence_order,
        "can_run_parallel": t.can_run_parallel,
        "requires_approval": t.requires_approval,
        "cost_usd": t.cost_usd,
    }


async def _run_workflow_background(
    project_id: str,
    org_id: str,
    objective: str,
    demo_mode: bool,
) -> None:
    """Background task that runs the LangGraph workflow."""
    from app.database import get_db_context
    engine = get_workflow_engine()

    try:
        final_state = await engine.run_project(
            project_id=project_id,
            organization_id=org_id,
            business_objective=objective,
            demo_mode=demo_mode,
        )

        # Update project in DB with results
        async with get_db_context() as db:
            result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
            project = result.scalar_one_or_none()
            if project:
                project.status = ProjectStatus.COMPLETED if final_state.get("deployment_success") else ProjectStatus.FAILED
                project.final_report = final_state.get("final_report", "")
                project.deployment_url = final_state.get("deployment_url", "")
                project.actual_cost_usd = final_state.get("total_cost_usd", 0.0)
                project.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        import structlog
        structlog.get_logger().error("Workflow background task failed", error=str(e), project_id=project_id)
