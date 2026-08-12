"""
LangGraph Graph Nodes — each node wraps an agent and updates workflow state.
"""
import json
from datetime import datetime, timezone
from typing import Any

from app.orchestration.state import WorkflowState
from app.agents.base import AgentContext
from app.agents.ceo.agent import CEOAgent
from app.agents.project_manager.agent import ProjectManagerAgent
from app.agents.developer.agent import DeveloperAgent
from app.agents.qa.agent import QAAgent
from app.agents.security.agent import SecurityAgent
from app.agents.devops.agent import DevOpsAgent
from app.agents.documentation.agent import DocumentationAgent
from app.agents.research.agent import ResearchAgent
from app.config import settings

import structlog
log = structlog.get_logger(__name__)

# ─── Agent singletons ────────────────────────────────────────────────────────
_ceo = CEOAgent()
_pm = ProjectManagerAgent()
_dev = DeveloperAgent()
_qa = QAAgent()
_security = SecurityAgent()
_devops = DevOpsAgent()
_docs = DocumentationAgent()
_research = ResearchAgent()


def _make_context(state: WorkflowState, task_description: str, input_data: dict = None) -> AgentContext:
    return AgentContext(
        project_id=state["project_id"],
        task_id=state.get("task_id", "main"),
        agent_type="workflow",
        organization_id=state["organization_id"],
        task_description=task_description,
        input_data=input_data or {},
        budget_remaining_usd=1.0,
        demo_mode=state.get("demo_mode", True),
    )


def _log_activity(agent: str, message: str, data: dict = None) -> dict:
    return {
        "agent": agent,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── CEO Node ─────────────────────────────────────────────────────────────────
async def ceo_node(state: WorkflowState) -> dict:
    ctx = _make_context(state, state["business_objective"])
    result = await _ceo.run(ctx)

    analysis = result.output.get("ceo_analysis", {})
    return {
        "ceo_analysis": analysis,
        "project_name": analysis.get("project_name", "AI Project"),
        "strategic_goals": analysis.get("strategic_goals", []),
        "required_departments": analysis.get("required_departments", []),
        "priority": analysis.get("priority", "medium"),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("CEO Agent", f"Analyzed business objective → {analysis.get('project_name', 'Project')}")],
    }


# ─── Research Node ────────────────────────────────────────────────────────────
async def research_node(state: WorkflowState) -> dict:
    ctx = _make_context(
        state,
        f"Research optimal technology stack for: {state['business_objective']}",
        {"ceo_analysis": state.get("ceo_analysis", {})},
    )
    result = await _research.run(ctx)

    return {
        "research_results": result.output.get("research", {}),
        "architecture_recommendation": result.output.get("architecture_recommendation", {}),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("Research Agent", "Architecture research complete")],
    }


# ─── Project Manager Node ─────────────────────────────────────────────────────
async def project_manager_node(state: WorkflowState) -> dict:
    input_data = {
        "ceo_analysis": state.get("ceo_analysis", {}),
        "research_results": state.get("research_results"),
        "architecture_recommendation": state.get("architecture_recommendation"),
    }
    ctx = _make_context(state, state["business_objective"], input_data)
    result = await _pm.run(ctx)

    tasks = result.output.get("tasks", [])
    return {
        "project_plan": result.output.get("project_plan", {}),
        "tasks": tasks,
        "parallel_groups": result.output.get("parallel_groups", []),
        "critical_path": result.output.get("critical_path", []),
        "approval_gates": result.output.get("approval_gates", []),
        "current_task_index": 0,
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("Project Manager", f"Created {len(tasks)} tasks and task dependency DAG")],
    }


# ─── Developer Node ───────────────────────────────────────────────────────────
async def developer_node(state: WorkflowState) -> dict:
    qa_feedback = None
    if state.get("qa_report") and not state.get("qa_approved"):
        qa_feedback = {
            "failed_tests": state.get("failed_tests", []),
            "bugs": state.get("bugs_found", []),
            "feedback": state["qa_report"].get("feedback_for_developer", ""),
        }

    input_data = {
        "task_type": "implementation",
        "architecture_proposal": str(state.get("architecture_recommendation", "")),
        "tech_stack": state.get("ceo_analysis", {}).get("tech_stack", {}),
        "qa_feedback": qa_feedback,
        "previous_implementation": state.get("implementation", {}),
        "project_name": state.get("project_name", ""),
    }
    ctx = _make_context(state, state["business_objective"], input_data)
    ctx.retry_count = state.get("developer_retry_count", 0)
    result = await _dev.run(ctx)

    impl = result.output.get("implementation", {})
    is_fix = qa_feedback is not None

    return {
        "implementation": impl,
        "files_generated": result.output.get("files", []),
        "branch_name": result.output.get("branch_name", "feature/impl"),
        "pr_title": result.output.get("pr_title", "Implementation"),
        "pr_description": result.output.get("pr_description", ""),
        "developer_retry_count": state.get("developer_retry_count", 0) + (1 if is_fix else 0),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("Developer", f"{'Fixed failures' if is_fix else 'Implemented'}: {len(result.output.get('files', []))} files")],
    }


# ─── QA Node ──────────────────────────────────────────────────────────────────
async def qa_node(state: WorkflowState) -> dict:
    input_data = {
        "implementation": state.get("implementation", {}),
        "files": state.get("files_generated", []),
        "task_description": state["business_objective"],
    }
    ctx = _make_context(state, "Run comprehensive tests on the implementation", input_data)
    result = await _qa.run(ctx)

    qa_report = result.output.get("qa_report", {})
    approved = result.output.get("approved_for_security", False)

    return {
        "qa_report": qa_report,
        "qa_approved": approved,
        "qa_retry_count": state.get("qa_retry_count", 0) + (0 if approved else 1),
        "failed_tests": result.output.get("failed_tests", []),
        "bugs_found": result.output.get("bugs", []),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("QA Agent", f"{'PASSED ✅' if approved else 'FAILED ❌'} — {qa_report.get('test_summary', {}).get('passed', 0)}/{qa_report.get('test_summary', {}).get('total_tests', 0)} tests passed")],
    }


# ─── Security Node ────────────────────────────────────────────────────────────
async def security_node(state: WorkflowState) -> dict:
    input_data = {
        "files": state.get("files_generated", []),
        "qa_report": state.get("qa_report", {}),
    }
    ctx = _make_context(state, "Perform comprehensive security audit", input_data)
    result = await _security.run(ctx)

    sec_report = result.output.get("security_report", {})
    approved = result.output.get("approved_for_deployment", False)

    return {
        "security_report": sec_report,
        "security_approved": approved,
        "security_findings": result.output.get("findings", []),
        "critical_security_issues": result.output.get("critical_count", 0),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("Security Agent", f"{'Cleared ✅' if approved else 'BLOCKED 🚨'} — {result.output.get('critical_count', 0)} critical, {result.output.get('high_count', 0)} high findings")],
    }


# ─── Documentation Node ───────────────────────────────────────────────────────
async def documentation_node(state: WorkflowState) -> dict:
    input_data = {
        "implementation": state.get("implementation", {}),
        "architecture_proposal": str(state.get("architecture_recommendation", "")),
        "qa_report": state.get("qa_report", {}),
        "security_report": state.get("security_report", {}),
        "project_name": state.get("project_name", ""),
    }
    ctx = _make_context(state, f"Generate documentation for {state.get('project_name', 'the project')}", input_data)
    result = await _docs.run(ctx)

    return {
        "documents": result.output.get("documents", []),
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("Documentation Agent", f"Generated {len(result.output.get('documents', []))} documentation files")],
    }


# ─── Human Approval Node ──────────────────────────────────────────────────────
async def human_approval_node(state: WorkflowState) -> dict:
    """
    Creates an approval request and waits.
    In demo mode — auto-approves after a short delay.
    In production — blocks until a human responds via the dashboard.
    """
    import asyncio, uuid

    if not state.get("approval_requested"):
        approval_id = str(uuid.uuid4())

        from app.memory.short_term import publish_event
        approval_event = {
            "event_type": "approval_required",
            "approval_id": approval_id,
            "project_id": state["project_id"],
            "project_name": state.get("project_name", "Project"),
            "action": "Production Deployment",
            "risk_level": "medium",
            "qa_passed": state.get("qa_approved", False),
            "security_passed": state.get("security_approved", False),
            "estimated_cost_usd": state.get("total_cost_usd", 0.0),
            "files_changed": len(state.get("files_generated", [])),
            "tests_passed": state.get("qa_report", {}).get("test_summary", {}).get("passed", 0),
        }
        await publish_event(f"project:{state['project_id']}:events", approval_event)
        await publish_event("global:events", approval_event)

        log.info("Approval requested", approval_id=approval_id, project=state["project_id"])

        if state.get("demo_mode", True):
            # Demo: auto-approve after 3 seconds
            await asyncio.sleep(3)
            return {
                "approval_requested": True,
                "approval_id": approval_id,
                "approval_status": "approved",
                "approval_notes": "Auto-approved in demo mode",
                "workflow_status": "running",
                "activity_log": [_log_activity("System", "🔐 Deployment approval requested — auto-approved (demo mode)")],
            }
        else:
            return {
                "approval_requested": True,
                "approval_id": approval_id,
                "approval_status": "pending",
                "workflow_status": "awaiting_approval",
                "activity_log": [_log_activity("System", "🔐 Deployment approval requested — awaiting human decision")],
            }

    return {}


# ─── DevOps Node ──────────────────────────────────────────────────────────────
async def devops_node(state: WorkflowState) -> dict:
    input_data = {
        "approval_granted": state.get("approval_status") == "approved",
        "security_report": state.get("security_report", {}),
        "project_name": state.get("project_name", "app"),
        "branch_name": state.get("branch_name", ""),
        "pr_title": state.get("pr_title", ""),
    }
    ctx = _make_context(state, f"Deploy {state.get('project_name', 'application')} to production", input_data)
    result = await _devops.run(ctx)

    return {
        "deployment_report": result.output.get("deployment_report", {}),
        "deployment_url": result.output.get("deployment_url", ""),
        "deployment_success": result.output.get("deployment_status") == "success",
        "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
        "activity_log": [_log_activity("DevOps Agent", f"{'🚀 Deployed successfully' if result.success else '❌ Deployment failed'}: {result.output.get('deployment_url', '')}")],
    }


# ─── CEO Final Report Node ────────────────────────────────────────────────────
async def ceo_final_report_node(state: WorkflowState) -> dict:
    ctx = _make_context(state, f"Generate final executive report for {state.get('project_name', 'project')}")

    project_results = {
        "project_name": state.get("project_name"),
        "business_objective": state["business_objective"],
        "status": "COMPLETED" if state.get("deployment_success") else "FAILED",
        "deployment_url": state.get("deployment_url", ""),
        "qa_summary": state.get("qa_report", {}).get("test_summary", {}),
        "security_summary": state.get("security_report", {}).get("scan_summary", {}),
        "documents_generated": len(state.get("documents", [])),
        "total_cost_usd": state.get("total_cost_usd", 0.0),
        "human_interventions": 1 if state.get("approval_status") == "approved" else 0,
        "activity_count": len(state.get("activity_log", [])),
    }

    final_report = await _ceo.generate_final_report(ctx, project_results)

    return {
        "final_report": final_report,
        "workflow_status": "completed",
        "activity_log": [_log_activity("CEO Agent", "📊 Final executive report generated — project complete!")],
    }


# ─── Error Handler Node ───────────────────────────────────────────────────────
async def error_handler_node(state: WorkflowState) -> dict:
    errors = state.get("errors", [])
    log.error("Workflow error handler triggered", errors=errors)

    return {
        "workflow_status": "failed",
        "activity_log": [_log_activity("System", f"❌ Workflow failed: {', '.join(errors[-3:]) if errors else 'Unknown error'}")],
    }


# ─── End Node ────────────────────────────────────────────────────────────────
async def end_node(state: WorkflowState) -> dict:
    status = state.get("workflow_status", "completed")
    return {
        "workflow_status": status,
        "activity_log": [_log_activity("System", f"Workflow ended with status: {status}")],
    }
