"""
LangGraph Workflow State — shared state object that flows through the graph.
All agents read from and write to this state.
"""
from typing import Any, Optional, Annotated
from typing_extensions import TypedDict
import operator


class WorkflowState(TypedDict):
    """
    The shared state object that flows through the LangGraph workflow.
    All agents read inputs from here and write outputs back here.
    """
    # ─── Identity ─────────────────────────────────────────────────────────────
    project_id: str
    organization_id: str
    task_id: str
    demo_mode: bool

    # ─── Business Input ───────────────────────────────────────────────────────
    business_objective: str

    # ─── CEO Output ───────────────────────────────────────────────────────────
    ceo_analysis: Optional[dict]
    project_name: str
    strategic_goals: list[str]
    required_departments: list[str]
    priority: str

    # ─── Project Manager Output ───────────────────────────────────────────────
    project_plan: Optional[dict]
    tasks: list[dict]
    parallel_groups: list[list[str]]
    critical_path: list[str]
    approval_gates: list[str]
    current_task_index: int

    # ─── Research Output ──────────────────────────────────────────────────────
    research_results: Optional[dict]
    architecture_recommendation: Optional[dict]

    # ─── Developer Output ─────────────────────────────────────────────────────
    implementation: Optional[dict]
    files_generated: list[dict]
    branch_name: str
    pr_title: str
    pr_description: str
    developer_retry_count: int

    # ─── QA Output ───────────────────────────────────────────────────────────
    qa_report: Optional[dict]
    qa_approved: bool
    qa_retry_count: int
    failed_tests: list[dict]
    bugs_found: list[dict]

    # ─── Security Output ──────────────────────────────────────────────────────
    security_report: Optional[dict]
    security_approved: bool
    security_findings: list[dict]
    critical_security_issues: int

    # ─── Documentation Output ────────────────────────────────────────────────
    documents: list[dict]

    # ─── Human Approval ───────────────────────────────────────────────────────
    approval_requested: bool
    approval_id: Optional[str]
    approval_status: str  # "pending" | "approved" | "rejected" | "changes_requested"
    approval_notes: str

    # ─── DevOps Output ────────────────────────────────────────────────────────
    deployment_report: Optional[dict]
    deployment_url: str
    deployment_success: bool

    # ─── Final Report ─────────────────────────────────────────────────────────
    final_report: str
    total_cost_usd: float
    workflow_status: str  # "running" | "completed" | "failed" | "awaiting_approval"

    # ─── Error Tracking ───────────────────────────────────────────────────────
    errors: Annotated[list[str], operator.add]
    activity_log: Annotated[list[dict], operator.add]


def initial_state(
    project_id: str,
    organization_id: str,
    business_objective: str,
    demo_mode: bool = True,
) -> WorkflowState:
    """Create the initial workflow state."""
    return WorkflowState(
        project_id=project_id,
        organization_id=organization_id,
        task_id="workflow_main",
        demo_mode=demo_mode,
        business_objective=business_objective,
        ceo_analysis=None,
        project_name="New Project",
        strategic_goals=[],
        required_departments=[],
        priority="medium",
        project_plan=None,
        tasks=[],
        parallel_groups=[],
        critical_path=[],
        approval_gates=[],
        current_task_index=0,
        research_results=None,
        architecture_recommendation=None,
        implementation=None,
        files_generated=[],
        branch_name="",
        pr_title="",
        pr_description="",
        developer_retry_count=0,
        qa_report=None,
        qa_approved=False,
        qa_retry_count=0,
        failed_tests=[],
        bugs_found=[],
        security_report=None,
        security_approved=False,
        security_findings=[],
        critical_security_issues=0,
        documents=[],
        approval_requested=False,
        approval_id=None,
        approval_status="pending",
        approval_notes="",
        deployment_report=None,
        deployment_url="",
        deployment_success=False,
        final_report="",
        total_cost_usd=0.0,
        workflow_status="running",
        errors=[],
        activity_log=[],
    )
