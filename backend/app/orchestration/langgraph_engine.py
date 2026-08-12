"""
LangGraph Engine — assembles and runs the complete AI Workforce workflow graph.

Graph Structure:
  START
    → CEO Agent
    → [Research Agent (if complex)] OR Project Manager
    → Project Manager
    → Developer Agent
    → QA Agent
    → [if FAIL] → Developer (loop, max 3 retries)
    → Security Agent
    → [if CRITICAL] → Developer (remediation)
    → Documentation Agent (parallel with Security)
    → Human Approval Gate
    → [if APPROVED] → DevOps Agent
    → CEO Final Report
    → END
"""
import asyncio
import uuid
from typing import Optional

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from app.orchestration.state import WorkflowState, initial_state
from app.orchestration.nodes import (
    ceo_node,
    research_node,
    project_manager_node,
    developer_node,
    qa_node,
    security_node,
    documentation_node,
    human_approval_node,
    devops_node,
    ceo_final_report_node,
    error_handler_node,
    end_node,
)
from app.orchestration.edges import (
    route_after_ceo,
    route_after_research,
    route_after_project_manager,
    route_after_developer,
    route_after_qa,
    route_after_security,
    route_after_human_approval,
    route_after_devops,
    route_error,
)

import structlog
log = structlog.get_logger(__name__)


def build_workflow_graph() -> StateGraph:
    """Construct the complete LangGraph workflow."""
    graph = StateGraph(WorkflowState)

    # ─── Add Nodes ────────────────────────────────────────────────────────────
    graph.add_node("ceo_agent", ceo_node)
    graph.add_node("research_agent", research_node)
    graph.add_node("project_manager", project_manager_node)
    graph.add_node("developer_agent", developer_node)
    graph.add_node("qa_agent", qa_node)
    graph.add_node("security_agent", security_node)
    graph.add_node("documentation_agent", documentation_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("devops_agent", devops_node)
    graph.add_node("ceo_final_report", ceo_final_report_node)
    graph.add_node("error_handler", error_handler_node)
    graph.add_node("end_workflow", end_node)

    # ─── Entry Point ──────────────────────────────────────────────────────────
    graph.add_edge(START, "ceo_agent")

    # ─── Conditional Edges ────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "ceo_agent",
        route_after_ceo,
        {
            "research_agent": "research_agent",
            "project_manager": "project_manager",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "research_agent",
        route_after_research,
        {"project_manager": "project_manager"},
    )

    graph.add_conditional_edges(
        "project_manager",
        route_after_project_manager,
        {
            "developer_agent": "developer_agent",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "developer_agent",
        route_after_developer,
        {
            "qa_agent": "qa_agent",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "qa_agent",
        route_after_qa,
        {
            "security_agent": "security_agent",
            "developer_agent": "developer_agent",  # Fix loop
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "security_agent",
        route_after_security,
        {
            "human_approval": "human_approval",
            "developer_agent": "developer_agent",  # Remediation
        },
    )

    # Documentation runs in parallel — triggered separately as needed
    graph.add_edge("documentation_agent", "human_approval")

    graph.add_conditional_edges(
        "human_approval",
        route_after_human_approval,
        {
            "devops_agent": "devops_agent",
            "developer_agent": "developer_agent",
            "end_workflow": "end_workflow",
        },
    )

    graph.add_conditional_edges(
        "devops_agent",
        route_after_devops,
        {
            "ceo_final_report": "ceo_final_report",
            "error_handler": "error_handler",
        },
    )

    graph.add_edge("ceo_final_report", "end_workflow")

    graph.add_conditional_edges(
        "error_handler",
        route_error,
        {"end_workflow": "end_workflow"},
    )

    graph.add_edge("end_workflow", END)

    return graph


# ─── Compiled Graph (singleton) ────────────────────────────────────────────────
_checkpointer = MemorySaver()
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_workflow_graph()
        _compiled_graph = graph.compile(checkpointer=_checkpointer)
    return _compiled_graph


# ─── Workflow Runner ──────────────────────────────────────────────────────────
class WorkflowEngine:
    """High-level interface for running the AI Workforce workflow."""

    def __init__(self):
        self.graph = get_compiled_graph()

    async def run_project(
        self,
        project_id: str,
        organization_id: str,
        business_objective: str,
        demo_mode: bool = True,
    ) -> WorkflowState:
        """
        Execute the complete AI Workforce workflow for a business objective.
        Returns the final workflow state.
        """
        state = initial_state(
            project_id=project_id,
            organization_id=organization_id,
            business_objective=business_objective,
            demo_mode=demo_mode,
        )

        config = {"configurable": {"thread_id": project_id}}

        log.info(
            "🚀 AI Workforce workflow starting",
            project_id=project_id,
            objective=business_objective[:100],
            demo_mode=demo_mode,
        )

        final_state = await self.graph.ainvoke(state, config=config)

        log.info(
            "✅ AI Workforce workflow complete",
            project_id=project_id,
            status=final_state.get("workflow_status"),
            cost=final_state.get("total_cost_usd", 0.0),
        )

        return final_state

    async def resume_workflow(
        self,
        project_id: str,
        approval_status: str,
        approval_notes: str = "",
    ) -> WorkflowState:
        """Resume a workflow that was waiting for human approval."""
        config = {"configurable": {"thread_id": project_id}}

        # Update state with approval decision
        update = {
            "approval_status": approval_status,
            "approval_notes": approval_notes,
            "workflow_status": "running",
        }

        final_state = await self.graph.ainvoke(update, config=config)
        return final_state

    async def get_workflow_state(self, project_id: str) -> Optional[WorkflowState]:
        """Get the current state of a running or completed workflow."""
        config = {"configurable": {"thread_id": project_id}}
        try:
            state_snapshot = self.graph.get_state(config)
            return state_snapshot.values if state_snapshot else None
        except Exception:
            return None


# ─── Global Engine ────────────────────────────────────────────────────────────
_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
