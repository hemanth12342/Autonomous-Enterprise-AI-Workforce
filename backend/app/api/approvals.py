"""
Approvals API — human-in-the-loop approval management.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.approval import Approval, ApprovalStatus
from app.models.user import User
from app.security.auth import get_current_user
from app.memory.short_term import publish_event
from app.orchestration.langgraph_engine import get_workflow_engine

router = APIRouter()


class ApprovalDecision(BaseModel):
    decision: str  # "approved" | "rejected" | "changes_requested"
    notes: Optional[str] = None


@router.get("/")
async def list_approvals(
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all approval requests."""
    query = select(Approval).where(
        Approval.project_id.in_(
            select(__import__("app.models.project", fromlist=["Project"]).Project.id).where(
                __import__("app.models.project", fromlist=["Project"]).Project.organization_id == current_user.organization_id
            )
        )
    ).order_by(Approval.created_at.desc())

    if status != "all":
        query = query.where(Approval.status == ApprovalStatus(status))

    result = await db.execute(query)
    approvals = result.scalars().all()
    return [_approval_to_dict(a) for a in approvals]


@router.post("/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve, reject, or request changes for an approval."""
    result = await db.execute(select(Approval).where(Approval.id == uuid.UUID(approval_id)))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status.value}")

    # Update approval
    approval.status = ApprovalStatus(decision.decision)
    approval.reviewer_id = current_user.id
    approval.reviewer_notes = decision.notes
    approval.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    # Publish event to resume workflow
    await publish_event(
        f"project:{approval.project_id}:events",
        {
            "event_type": "approval_decision",
            "approval_id": approval_id,
            "decision": decision.decision,
            "notes": decision.notes,
            "reviewer": current_user.full_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    await publish_event("global:events", {
        "event_type": "approval_decision",
        "message": f"Human {'approved' if decision.decision == 'approved' else 'rejected'} deployment",
        "decision": decision.decision,
        "reviewer": current_user.full_name,
    })

    # Resume workflow if project has an active LangGraph thread
    if decision.decision in ["approved", "rejected", "changes_requested"]:
        try:
            engine = get_workflow_engine()
            await engine.resume_workflow(
                str(approval.project_id),
                approval_status=decision.decision,
                approval_notes=decision.notes or "",
            )
        except Exception:
            pass  # Workflow may use polling instead

    return {"message": f"Approval {decision.decision}", "approval_id": approval_id}


def _approval_to_dict(a: Approval) -> dict:
    return {
        "id": str(a.id),
        "project_id": str(a.project_id) if a.project_id else None,
        "requesting_agent": a.requesting_agent,
        "action_type": a.action_type,
        "action_description": a.action_description,
        "risk_level": a.risk_level.value,
        "status": a.status.value,
        "files_changed": a.files_changed,
        "tests_passed": a.tests_passed,
        "security_passed": a.security_passed,
        "estimated_cost_usd": a.estimated_cost_usd,
        "summary": a.summary,
        "reviewer_notes": a.reviewer_notes,
        "created_at": a.created_at.isoformat(),
        "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
    }
