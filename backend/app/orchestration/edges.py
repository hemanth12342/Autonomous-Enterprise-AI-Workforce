"""
LangGraph Conditional Edges — routing logic between agent nodes.
"""
from app.orchestration.state import WorkflowState
from app.config import settings


def route_after_ceo(state: WorkflowState) -> str:
    """CEO → Research (if complex) or Project Manager (standard)."""
    if state.get("ceo_analysis") is None:
        return "error_handler"
    complexity = state["ceo_analysis"].get("estimated_complexity", "moderate")
    if complexity == "complex":
        return "research_agent"
    return "project_manager"


def route_after_research(state: WorkflowState) -> str:
    """Research → Project Manager (always)."""
    return "project_manager"


def route_after_project_manager(state: WorkflowState) -> str:
    """Project Manager → Developer (always)."""
    if not state.get("tasks"):
        return "error_handler"
    return "developer_agent"


def route_after_developer(state: WorkflowState) -> str:
    """Developer → QA (always after implementation)."""
    if not state.get("implementation"):
        return "error_handler"
    return "qa_agent"


def route_after_qa(state: WorkflowState) -> str:
    """
    QA decision:
    - PASSED → security_agent
    - FAILED + retries available → developer_agent (fix loop)
    - FAILED + max retries → error_handler
    """
    if state.get("qa_approved"):
        return "security_agent"

    retry_count = state.get("qa_retry_count", 0)
    if retry_count < settings.max_agent_retries:
        return "developer_agent"
    return "error_handler"  # Max retries exceeded → escalate


def route_after_security(state: WorkflowState) -> str:
    """
    Security decision:
    - NO CRITICAL issues → human_approval gate
    - CRITICAL issues → developer_agent (remediation)
    - MAX retries exceeded → error_handler
    """
    if state.get("security_approved"):
        return "human_approval"

    # Security can send back to developer for fixes
    return "developer_agent"


def route_after_human_approval(state: WorkflowState) -> str:
    """
    Human approval decision:
    - APPROVED → devops_agent
    - REJECTED → end (cancelled)
    - CHANGES_REQUESTED → developer_agent
    - PENDING → wait (should not reach this in graph)
    """
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "devops_agent"
    elif status == "rejected":
        return "end_workflow"
    elif status == "changes_requested":
        return "developer_agent"
    else:
        # Still pending — wait
        return "human_approval"


def route_after_devops(state: WorkflowState) -> str:
    """
    DevOps decision:
    - SUCCESS → ceo_final_report
    - FAILED → error_handler (DevOps recovery → escalate)
    """
    if state.get("deployment_success"):
        return "ceo_final_report"
    return "error_handler"


def route_error(state: WorkflowState) -> str:
    """Error handler — always goes to end after logging."""
    return "end_workflow"
