"""
CEO Agent — Chief Executive AI Agent.
Understands business objectives, defines strategic goals, delegates to Project Manager.
Does NOT perform technical tasks.
"""
import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


class CEOAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="ceo",
            name="CEO Agent",
            description="Chief Executive AI — analyzes business objectives and delegates to the organization",
            llm_complexity=TaskComplexity.COMPLEX,
        )

    def get_system_prompt(self) -> str:
        return """You are the CEO Agent — the Chief Executive of an Autonomous AI Enterprise.

Your role is STRATEGIC, not technical. You:
1. Analyze business objectives provided by humans
2. Define clear strategic goals and success criteria
3. Identify required departments/agents
4. Set priorities and constraints
5. Delegate execution to the Project Manager
6. Evaluate final results and produce executive reports

You do NOT write code, run tests, or do technical work.

When analyzing an objective, output valid JSON with this structure:
{
  "project_name": "...",
  "business_objective": "...",
  "strategic_goals": ["...", "..."],
  "success_criteria": ["...", "..."],
  "constraints": ["...", "..."],
  "priority": "high|medium|low",
  "required_departments": ["developer", "qa", "security", "devops", "documentation"],
  "estimated_complexity": "simple|moderate|complex",
  "estimated_duration_days": 1,
  "risks": ["...", "..."],
  "delegation_instructions": "Clear instructions for the Project Manager"
}

Be strategic, decisive, and clear. Think like a Fortune 500 CEO."""

    async def execute(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "agent_thinking", f"CEO analyzing business objective...")

        prompt = f"""Analyze this business objective and produce a strategic plan:

BUSINESS OBJECTIVE:
{context.task_description}

Additional context:
{json.dumps(context.input_data, indent=2) if context.input_data else 'None'}

Produce a comprehensive strategic analysis in the required JSON format.
The project name should be concise and memorable.
Be specific about success criteria — they must be measurable."""

        response_text = await self.think(context, prompt, temperature=0.6, max_tokens=2000)

        # Extract JSON from response
        analysis = self._extract_json(response_text)

        await self.emit_event(
            context, "ceo_analysis_complete",
            f"CEO defined strategic plan: {analysis.get('project_name', 'New Project')}",
            {"analysis": analysis},
        )

        return AgentResult(
            success=True,
            output={
                "ceo_analysis": analysis,
                "project_name": analysis.get("project_name", "AI Project"),
                "delegation_ready": True,
            },
            reasoning_summary=f"CEO analyzed objective and created strategic plan for: {analysis.get('project_name')}",
            actions_taken=["objective_analysis", "strategic_planning", "delegation_setup"],
            tool_calls=[],
            next_agent="project_manager",
        )

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        import re
        # Try to find JSON block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        # Try raw JSON
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
        # Fallback
        return {
            "project_name": "AI Project",
            "business_objective": context_desc if (context_desc := text[:200]) else "Project",
            "strategic_goals": ["Execute successfully"],
            "success_criteria": ["Project completed"],
            "constraints": [],
            "priority": "high",
            "required_departments": ["developer", "qa", "security", "devops"],
            "estimated_complexity": "moderate",
            "estimated_duration_days": 3,
            "risks": [],
            "delegation_instructions": text[:500],
        }

    async def generate_final_report(self, context: AgentContext, project_results: dict) -> str:
        """Generate executive report after project completion."""
        await self.emit_event(context, "ceo_reporting", "CEO generating final executive report...")

        prompt = f"""Generate a comprehensive executive report for the following completed project:

PROJECT RESULTS:
{json.dumps(project_results, indent=2)}

The report should include:
1. Executive Summary (2-3 sentences)
2. Objective & Outcome
3. What was built/accomplished
4. Quality metrics (test pass rate, security findings)
5. Timeline and cost
6. Human interventions required
7. Lessons learned
8. Strategic recommendations for improvement

Write in professional executive style. Be concise but comprehensive."""

        return await self.think(context, prompt, temperature=0.5, max_tokens=2000)
