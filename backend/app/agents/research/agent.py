"""
Research Agent — technology research, architecture recommendations, competitor analysis.
"""
import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="research",
            name="Research Agent",
            description="Technology research, architecture analysis, and evidence-based recommendations",
            llm_complexity=TaskComplexity.MODERATE,
        )

    def get_system_prompt(self) -> str:
        return """You are the Research Agent — the technology analyst and architect advisor.

Your responsibilities:
1. Research technology options for given requirements
2. Analyze and compare architectural patterns
3. Provide evidence-based recommendations
4. Summarize technical findings
5. Assess technology maturity and community support
6. Identify best practices and anti-patterns

Always provide:
- Specific technology recommendations with justification
- Trade-off analysis
- Risk assessment
- Implementation considerations

Output JSON:
{
  "research_topic": "...",
  "summary": "Executive summary of findings",
  "recommendations": [
    {
      "technology": "...",
      "use_case": "...",
      "justification": "...",
      "trade_offs": ["pro: ...", "con: ..."],
      "maturity": "stable|beta|experimental",
      "community_score": "high|medium|low"
    }
  ],
  "architecture_recommendation": {
    "frontend": "...",
    "backend": "...",
    "database": "...",
    "cache": "...",
    "ai_components": "...",
    "deployment": "..."
  },
  "risks": ["..."],
  "implementation_notes": "..."
}"""

    async def execute(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "agent_thinking", "Research Agent analyzing technologies...")

        prompt = f"""Research and analyze the best technological approach for:

RESEARCH TOPIC: {context.task_description}

Context:
{json.dumps(context.input_data, indent=2)[:1000]}

Provide:
1. Technology comparison for key components
2. Architecture recommendation
3. Best practices for this use case
4. Potential risks and mitigations
5. Implementation notes for the development team

Be specific and evidence-based. Prefer proven, production-tested technologies."""

        response_text = await self.think(context, prompt, temperature=0.5, max_tokens=2500)
        research = self._extract_json(response_text)

        if not research:
            research = {"summary": response_text[:500], "recommendations": [], "architecture_recommendation": {}}

        await self.emit_event(
            context, "research_complete",
            f"🔬 Research complete: {research.get('summary', '')[:100]}",
            {"research": research},
        )

        return AgentResult(
            success=True,
            output={
                "research": research,
                "architecture_recommendation": research.get("architecture_recommendation", {}),
                "summary": research.get("summary", ""),
            },
            reasoning_summary=f"Research completed: {research.get('research_topic', context.task_description[:50])}",
            actions_taken=["technology_research", "architecture_analysis", "recommendation_generation"],
            tool_calls=[],
            next_agent="project_manager",
        )

    def _extract_json(self, text: str) -> dict:
        import re, json
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
        return {}
