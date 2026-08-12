"""
Demo API — one-click autonomous company simulation.
Runs the complete AI Workforce workflow with a pre-set business objective.
"""
import uuid
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, get_db_context
from app.models.project import Project, ProjectStatus, ProjectPriority
from app.models.user import User, Organization
from app.security.auth import get_current_user
from app.orchestration.langgraph_engine import get_workflow_engine
from app.memory.short_term import publish_event

router = APIRouter()

DEMO_OBJECTIVES = {
    "customer_support": "Build an AI-powered customer support platform that allows customers to ask questions about our product documentation using RAG. The system should show source citations, support escalation to human agents, and deploy securely.",
    "ecommerce": "Build a modern e-commerce platform with product catalog, shopping cart, payment integration, and an AI recommendation engine.",
    "analytics": "Build a real-time analytics dashboard that ingests data from multiple sources and provides AI-powered insights and forecasting.",
    "saas": "Build a B2B SaaS application with multi-tenant architecture, subscription billing, and role-based access control.",
}


@router.post("/start")
async def start_demo(
    background_tasks: BackgroundTasks,
    objective_key: str = "customer_support",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    One-click demo — starts the complete AI Workforce autonomous workflow.
    Watch the dashboard for real-time agent activity.
    """
    objective = DEMO_OBJECTIVES.get(objective_key, DEMO_OBJECTIVES["customer_support"])

    # Create demo project
    project = Project(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        name=f"Demo: {objective_key.replace('_', ' ').title()} Platform",
        business_objective=objective,
        description="Autonomous AI Workforce demo project",
        status=ProjectStatus.PLANNING,
        priority=ProjectPriority.HIGH,
        budget_usd=5.00,
        is_demo=True,
        started_at=datetime.now(timezone.utc),
    )
    db.add(project)
    await db.flush()

    project_id = str(project.id)

    # Announce demo start
    await publish_event("global:events", {
        "event_type": "demo_started",
        "project_id": project_id,
        "project_name": project.name,
        "message": f"🚀 Autonomous Company Demo Started: {project.name}",
        "objective": objective[:150],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Run in background
    background_tasks.add_task(
        _run_demo_workflow,
        project_id,
        str(current_user.organization_id),
        objective,
    )

    return {
        "message": "🚀 Autonomous Company started! Watch the dashboard for live agent activity.",
        "project_id": project_id,
        "project_name": project.name,
        "objective": objective[:200],
        "websocket_url": f"/api/ws/project/{project_id}",
        "dashboard_url": f"/projects/{project_id}",
    }


@router.get("/objectives")
async def list_demo_objectives():
    """List available demo business objectives."""
    return {
        key: {"key": key, "title": key.replace("_", " ").title(), "objective": obj[:200]}
        for key, obj in DEMO_OBJECTIVES.items()
    }


async def _run_demo_workflow(project_id: str, org_id: str, objective: str) -> None:
    """Background task for demo workflow."""
    engine = get_workflow_engine()
    from app.database import get_db_context

    try:
        final_state = await engine.run_project(
            project_id=project_id,
            organization_id=org_id,
            business_objective=objective,
            demo_mode=True,
        )

        # Save results to DB
        async with get_db_context() as db:
            result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
            project = result.scalar_one_or_none()
            if project:
                project.status = ProjectStatus.COMPLETED if final_state.get("deployment_success") else ProjectStatus.FAILED
                project.final_report = final_state.get("final_report", "")
                project.deployment_url = final_state.get("deployment_url", "")
                project.actual_cost_usd = final_state.get("total_cost_usd", 0.0)
                project.completed_at = datetime.now(timezone.utc)

        await publish_event("global:events", {
            "event_type": "demo_completed",
            "project_id": project_id,
            "message": f"✅ Demo Complete! Total cost: ${final_state.get('total_cost_usd', 0.0):.4f}",
            "deployment_url": final_state.get("deployment_url", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        await publish_event("global:events", {
            "event_type": "demo_error",
            "project_id": project_id,
            "message": f"❌ Demo error: {str(e)[:100]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
