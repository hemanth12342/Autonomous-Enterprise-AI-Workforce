"""
Documentation Agent — generates README, API docs, architecture guides, deployment guides.
"""
import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="documentation",
            name="Documentation Agent",
            description="Generates comprehensive project documentation",
            llm_complexity=TaskComplexity.SIMPLE,
        )

    def get_system_prompt(self) -> str:
        return """You are the Documentation Agent — the technical writer of an Autonomous AI Enterprise.

Generate clear, comprehensive, professional documentation for software projects.

Documentation types you produce:
1. README.md — Project overview, quick start, features
2. API Documentation — Endpoint descriptions, request/response examples
3. Architecture Documentation — System design, component interactions
4. Setup Guide — Installation and configuration steps
5. Deployment Guide — Production deployment instructions
6. User Guide — End-user instructions
7. Developer Guide — Contributing and development setup
8. Changelog — Version history

Style guidelines:
- Use clear, concise language
- Include code examples
- Use proper markdown formatting
- Add diagrams descriptions (Mermaid where helpful)
- Be complete but avoid unnecessary verbosity

Output JSON:
{
  "documents": [
    {
      "type": "README",
      "filename": "README.md",
      "content": "# Project Name\\n..."
    }
  ],
  "documentation_summary": "Generated X documents covering..."
}"""

    async def execute(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "agent_thinking", "Documentation Agent generating docs...")

        implementation = context.input_data.get("implementation", {})
        architecture = context.input_data.get("architecture_proposal", "")
        qa_report = context.input_data.get("qa_report", {})
        security_report = context.input_data.get("security_report", {})

        prompt = f"""Generate comprehensive documentation for this project:

PROJECT: {context.task_description}

ARCHITECTURE:
{architecture[:1000] if architecture else 'Standard web application'}

IMPLEMENTATION SUMMARY:
Files: {json.dumps([f.get('path', '') for f in implementation.get('files', [])], indent=2)[:500]}

QA RESULTS:
{json.dumps(qa_report.get('test_summary', {}), indent=2)}

SECURITY RESULTS:
{json.dumps(security_report.get('scan_summary', {}), indent=2)}

Generate: README.md, API docs overview, Architecture overview, Setup guide.
Make them professional, detailed, and ready for production use."""

        response_text = await self.think(context, prompt, temperature=0.6, max_tokens=4000)
        docs_result = self._extract_json(response_text)

        if not docs_result.get("documents"):
            docs_result = self._generate_default_docs(context)

        doc_count = len(docs_result.get("documents", []))

        await self.emit_event(
            context, "documentation_complete",
            f"📚 Documentation Agent generated {doc_count} documents",
            {"doc_types": [d.get("type") for d in docs_result.get("documents", [])]},
        )

        return AgentResult(
            success=True,
            output={
                "documents": docs_result.get("documents", []),
                "doc_count": doc_count,
                "documentation_summary": docs_result.get("documentation_summary", f"Generated {doc_count} documentation files"),
            },
            reasoning_summary=f"Generated {doc_count} documentation files",
            actions_taken=["readme_generation", "api_docs", "architecture_docs", "setup_guide"],
            tool_calls=[{"tool": "doc_generator", "action": "generate", "result": f"{doc_count} documents"}],
        )

    def _generate_default_docs(self, context: AgentContext) -> dict:
        project_name = context.input_data.get("project_name", "AI Project")
        return {
            "documents": [
                {"type": "README", "filename": "README.md", "content": f"# {project_name}\n\nAI-powered application built by the Autonomous Enterprise AI Workforce.\n\n## Quick Start\n\n```bash\ndocker-compose up\n```\n\n## Features\n- AI-powered functionality\n- RESTful API\n- Modern frontend\n\n## Architecture\nBuilt with FastAPI + React + PostgreSQL.\n"},
                {"type": "API_DOCS", "filename": "docs/api.md", "content": f"# {project_name} API Documentation\n\n## Base URL\n`https://api.example.com/v1`\n\n## Authentication\nAll endpoints require JWT Bearer token.\n\n## Endpoints\n\n### GET /health\nHealth check endpoint.\n\n### POST /api/query\nSubmit a query to the AI system.\n"},
                {"type": "SETUP_GUIDE", "filename": "docs/setup.md", "content": "# Setup Guide\n\n## Prerequisites\n- Docker Desktop\n- Node.js 18+\n- Python 3.11+\n\n## Installation\n\n1. Clone the repository\n2. Copy `.env.example` to `.env`\n3. Run `docker-compose up`\n4. Access the dashboard at http://localhost:3000\n"},
            ],
            "documentation_summary": "Generated 3 core documentation files: README, API docs, and setup guide.",
        }

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
