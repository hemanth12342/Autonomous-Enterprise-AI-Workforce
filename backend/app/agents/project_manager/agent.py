"""
Project Manager Agent — converts CEO objectives into executable task DAGs.
Coordinates the workforce, tracks progress, detects blocks, escalates.
"""
import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


TASK_TEMPLATE = {
    "id": "task_{n}",
    "title": "...",
    "description": "...",
    "task_type": "...",
    "assigned_agent": "...",
    "priority": "high|medium|low",
    "depends_on": [],
    "can_run_parallel": False,
    "estimated_minutes": 30,
    "requires_approval": False,
}


class ProjectManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="project_manager",
            name="Project Manager",
            description="Converts CEO objectives into task DAGs, coordinates the AI workforce",
            llm_complexity=TaskComplexity.MODERATE,
        )

    def get_system_prompt(self) -> str:
        return """You are the Project Manager Agent — the workforce coordinator of an Autonomous AI Enterprise.

Your responsibilities:
1. Convert CEO strategic goals into concrete, executable tasks
2. Create task dependency graphs (DAGs) — which tasks block which
3. Assign each task to the correct specialist agent
4. Identify tasks that can run in parallel (concurrency)
5. Track progress and detect blocked tasks
6. Reassign and escalate as needed
7. Coordinate communication between agents

AVAILABLE AGENTS:
- developer: Code generation, GitHub operations, bug fixing
- qa: Testing, quality review, test report generation
- devops: Docker builds, Kubernetes deployment, monitoring
- security: SAST, dependency scanning, secret detection
- documentation: README, API docs, guides
- research: Technology research, architecture recommendations
- support: Customer support with RAG

STANDARD WORKFLOW (always follow this order):
1. research (optional) → architecture research
2. developer → requirements + architecture design
3. developer (parallel with database) → backend implementation
4. developer (parallel) → frontend implementation
5. developer (parallel) → database design + migrations
6. qa → testing (depends on: developer tasks)
7. security → security audit (depends on: qa)
8. documentation → generate docs (parallel with security)
9. [HUMAN APPROVAL GATE]
10. devops → deployment (depends on: approval)
11. devops → monitoring setup

Output valid JSON with this structure:
{
  "project_plan": {
    "name": "...",
    "description": "...",
    "total_tasks": 10,
    "estimated_total_hours": 4
  },
  "tasks": [
    {
      "id": "task_1",
      "title": "Requirements Analysis",
      "description": "Detailed task description...",
      "task_type": "requirements",
      "assigned_agent": "developer",
      "priority": "high",
      "depends_on": [],
      "can_run_parallel": false,
      "estimated_minutes": 20,
      "requires_approval": false,
      "sequence_order": 1
    }
  ],
  "parallel_groups": [["task_3", "task_4", "task_5"]],
  "critical_path": ["task_1", "task_2", "task_5", "task_6", "task_8", "task_10"],
  "approval_gates": ["task_9"],
  "coordination_notes": "..."
}"""

    async def execute(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "agent_thinking", "Project Manager creating execution plan...")

        ceo_analysis = context.input_data.get("ceo_analysis", {})

        prompt = f"""Create a detailed project execution plan for this strategic objective:

CEO STRATEGIC ANALYSIS:
{json.dumps(ceo_analysis, indent=2)}

ORIGINAL OBJECTIVE:
{context.task_description}

Create a comprehensive task DAG. Requirements:
1. Every task must have a clear agent assignment
2. Identify all dependencies (task A blocks task B)
3. Mark tasks that can run in parallel
4. Include a human approval gate before production deployment
5. Ensure QA runs before Security
6. Ensure Security runs before Deployment
7. Documentation can run in parallel with Security
8. Be specific in task descriptions — agents will execute these directly

Generate 8-14 tasks. More complex projects need more tasks."""

        response_text = await self.think(context, prompt, temperature=0.5, max_tokens=3000)
        plan = self._extract_json(response_text)

        tasks = plan.get("tasks", [])
        await self.emit_event(
            context, "pm_plan_created",
            f"Project Manager created {len(tasks)} tasks",
            {"task_count": len(tasks), "plan": plan},
        )

        return AgentResult(
            success=True,
            output={
                "project_plan": plan,
                "tasks": tasks,
                "parallel_groups": plan.get("parallel_groups", []),
                "critical_path": plan.get("critical_path", []),
                "approval_gates": plan.get("approval_gates", []),
            },
            reasoning_summary=f"Created execution plan with {len(tasks)} tasks",
            actions_taken=["task_decomposition", "dag_creation", "agent_assignment"],
            tool_calls=[],
            next_agent=tasks[0].get("assigned_agent") if tasks else "developer",
        )

    def _extract_json(self, text: str) -> dict:
        import re
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
        # Default fallback plan
        return {
            "project_plan": {"name": "AI Project", "description": "Autonomous project", "total_tasks": 8, "estimated_total_hours": 4},
            "tasks": self._default_tasks(),
            "parallel_groups": [],
            "critical_path": ["task_1", "task_2", "task_3", "task_4", "task_5", "task_6"],
            "approval_gates": ["task_5"],
            "coordination_notes": "Standard development workflow",
        }

    def _default_tasks(self) -> list:
        return [
            {"id": "task_1", "title": "Requirements Analysis", "description": "Analyze and document requirements", "task_type": "requirements", "assigned_agent": "developer", "priority": "high", "depends_on": [], "can_run_parallel": False, "estimated_minutes": 20, "requires_approval": False, "sequence_order": 1},
            {"id": "task_2", "title": "Architecture Design", "description": "Design system architecture", "task_type": "architecture", "assigned_agent": "developer", "priority": "high", "depends_on": ["task_1"], "can_run_parallel": False, "estimated_minutes": 30, "requires_approval": False, "sequence_order": 2},
            {"id": "task_3", "title": "Backend Development", "description": "Implement backend API", "task_type": "backend_development", "assigned_agent": "developer", "priority": "high", "depends_on": ["task_2"], "can_run_parallel": True, "estimated_minutes": 60, "requires_approval": False, "sequence_order": 3},
            {"id": "task_4", "title": "Frontend Development", "description": "Implement frontend UI", "task_type": "frontend_development", "assigned_agent": "developer", "priority": "high", "depends_on": ["task_2"], "can_run_parallel": True, "estimated_minutes": 60, "requires_approval": False, "sequence_order": 3},
            {"id": "task_5", "title": "Testing", "description": "Run comprehensive tests", "task_type": "testing", "assigned_agent": "qa", "priority": "high", "depends_on": ["task_3", "task_4"], "can_run_parallel": False, "estimated_minutes": 30, "requires_approval": False, "sequence_order": 4},
            {"id": "task_6", "title": "Security Audit", "description": "Scan for vulnerabilities", "task_type": "security_audit", "assigned_agent": "security", "priority": "high", "depends_on": ["task_5"], "can_run_parallel": False, "estimated_minutes": 20, "requires_approval": False, "sequence_order": 5},
            {"id": "task_7", "title": "Documentation", "description": "Generate project documentation", "task_type": "documentation", "assigned_agent": "documentation", "priority": "medium", "depends_on": ["task_5"], "can_run_parallel": True, "estimated_minutes": 20, "requires_approval": False, "sequence_order": 5},
            {"id": "task_8", "title": "Production Deployment", "description": "Deploy to production", "task_type": "deployment", "assigned_agent": "devops", "priority": "high", "depends_on": ["task_6", "task_7"], "can_run_parallel": False, "estimated_minutes": 20, "requires_approval": True, "sequence_order": 6},
        ]
