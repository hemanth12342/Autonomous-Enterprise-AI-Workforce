"""
Agents API — agent status, metrics, and execution.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.agent import Agent, AgentType, AgentStatus
from app.models.user import User
from app.security.auth import get_current_user

router = APIRouter()

# Static agent registry — describes all available agents
AGENT_REGISTRY = [
    {
        "agent_type": "ceo",
        "name": "CEO Agent",
        "description": "Chief Executive — strategic analysis, delegation, executive reporting",
        "icon": "🧠",
        "color": "#6366f1",
        "capabilities": ["strategic_analysis", "delegation", "executive_reporting"],
    },
    {
        "agent_type": "project_manager",
        "name": "Project Manager",
        "description": "Coordinates the workforce — task planning, DAG creation, progress tracking",
        "icon": "📋",
        "color": "#8b5cf6",
        "capabilities": ["task_planning", "dag_creation", "coordination", "escalation"],
    },
    {
        "agent_type": "developer",
        "name": "Developer Agent",
        "description": "Full-stack developer — code generation, GitHub, bug fixing",
        "icon": "💻",
        "color": "#06b6d4",
        "capabilities": ["code_generation", "github_operations", "bug_fixing", "testing"],
    },
    {
        "agent_type": "qa",
        "name": "QA Agent",
        "description": "Quality assurance — test generation, execution, defect reporting",
        "icon": "🧪",
        "color": "#10b981",
        "capabilities": ["test_generation", "test_execution", "defect_reporting", "coverage_analysis"],
    },
    {
        "agent_type": "security",
        "name": "Security Agent",
        "description": "Security analysis — SAST, dependency scanning, secret detection",
        "icon": "🔒",
        "color": "#f59e0b",
        "capabilities": ["sast", "dependency_scan", "secret_detection", "auth_review"],
    },
    {
        "agent_type": "devops",
        "name": "DevOps Agent",
        "description": "Infrastructure — Docker, Kubernetes, deployment, monitoring",
        "icon": "🚀",
        "color": "#ef4444",
        "capabilities": ["docker_build", "kubernetes_deploy", "monitoring", "incident_response"],
    },
    {
        "agent_type": "documentation",
        "name": "Documentation Agent",
        "description": "Technical writer — README, API docs, architecture guides",
        "icon": "📚",
        "color": "#84cc16",
        "capabilities": ["readme", "api_docs", "architecture_docs", "setup_guides"],
    },
    {
        "agent_type": "support",
        "name": "Support Agent",
        "description": "Customer support — RAG-powered Q&A, ticket management",
        "icon": "🎧",
        "color": "#f97316",
        "capabilities": ["rag_qa", "ticket_creation", "escalation", "knowledge_search"],
    },
    {
        "agent_type": "research",
        "name": "Research Agent",
        "description": "Technology research — architecture analysis, recommendations",
        "icon": "🔬",
        "color": "#a78bfa",
        "capabilities": ["tech_research", "architecture_analysis", "competitor_research"],
    },
]


@router.get("/")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all AI agents with their current status and metrics."""
    # Get DB records
    result = await db.execute(
        select(Agent).where(Agent.organization_id == current_user.organization_id)
    )
    db_agents = {a.agent_type.value: a for a in result.scalars().all()}

    agents = []
    for reg in AGENT_REGISTRY:
        atype = reg["agent_type"]
        db_agent = db_agents.get(atype)

        agents.append({
            **reg,
            "status": db_agent.status.value if db_agent else "idle",
            "tasks_completed": db_agent.tasks_completed if db_agent else 0,
            "tasks_failed": db_agent.tasks_failed if db_agent else 0,
            "total_cost_usd": db_agent.total_cost_usd if db_agent else 0.0,
            "success_rate": db_agent.success_rate if db_agent else 0.0,
            "current_task": db_agent.current_task_description if db_agent else None,
        })

    return agents


@router.get("/{agent_type}/runs")
async def get_agent_runs(
    agent_type: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent runs for a specific agent type."""
    from app.models.agent import AgentRun
    result = await db.execute(
        select(AgentRun)
        .join(Agent)
        .where(Agent.organization_id == current_user.organization_id)
        .where(Agent.agent_type == AgentType(agent_type))
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "cost_usd": r.cost_usd,
            "duration_seconds": r.duration_seconds,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]
