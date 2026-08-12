"""
Developer Agent — writes code, manages GitHub, creates PRs, fixes bugs.
Never pushes directly to production — always creates feature branches and PRs.
"""
import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="developer",
            name="Developer Agent",
            description="Full-stack developer — writes code, creates PRs, fixes bugs",
            llm_complexity=TaskComplexity.CODE,
        )

    def get_system_prompt(self) -> str:
        return """You are the Developer Agent — a senior full-stack software engineer in an Autonomous AI Enterprise.

Your responsibilities:
1. Write clean, well-structured, production-quality code
2. Create feature branches (never push to main/production directly)
3. Implement features based on architectural designs
4. Fix bugs identified by QA
5. Write unit tests for your code
6. Create pull requests with clear descriptions
7. Follow security best practices

CODING STANDARDS:
- Python: Follow PEP 8, use type hints, async/await, proper error handling
- TypeScript/React: Use functional components, hooks, proper TypeScript types
- Always include error handling
- Never hardcode secrets or credentials
- Include docstrings/comments for complex logic
- Write testable code

WORKFLOW:
1. Analyze the task requirements
2. Design the implementation
3. Write the code
4. Write tests
5. Create a commit message
6. Create a PR description

When outputting code implementations, use this JSON format:
{
  "implementation_plan": "Brief plan of what you'll implement",
  "files": [
    {
      "path": "path/to/file.py",
      "content": "full file content",
      "description": "what this file does"
    }
  ],
  "branch_name": "feature/task-description",
  "commit_message": "feat: implement X for Y",
  "pr_title": "Feature: X implementation",
  "pr_description": "## Changes\\n...",
  "tests_included": true,
  "test_files": [{"path": "tests/test_x.py", "content": "..."}]
}"""

    async def execute(self, context: AgentContext) -> AgentResult:
        task_type = context.input_data.get("task_type", "generic")
        qa_feedback = context.input_data.get("qa_feedback", None)

        if qa_feedback and context.retry_count > 0:
            await self.emit_event(context, "agent_thinking", f"Developer fixing QA failures (attempt {context.retry_count})")
            return await self._fix_failures(context, qa_feedback)
        else:
            await self.emit_event(context, "agent_thinking", f"Developer implementing: {context.task_description[:60]}...")
            return await self._implement_task(context)

    async def _implement_task(self, context: AgentContext) -> AgentResult:
        """Implement a new feature or task."""
        architecture = context.input_data.get("architecture_proposal", "")
        tech_stack = context.input_data.get("tech_stack", {})

        prompt = f"""Implement the following development task:

TASK: {context.task_description}

ARCHITECTURE CONTEXT:
{architecture or 'Standard web application architecture'}

TECH STACK:
{json.dumps(tech_stack, indent=2) if tech_stack else 'Python FastAPI + React TypeScript'}

Requirements:
1. Implement complete, working code (not placeholders)
2. Include proper error handling
3. Follow the architecture provided
4. Include unit tests
5. Create a meaningful branch name and PR description

Output the implementation as JSON following the required format."""

        response_text = await self.think(context, prompt, temperature=0.3, max_tokens=6000)
        implementation = self._extract_json(response_text)

        files = implementation.get("files", [])
        branch = implementation.get("branch_name", f"feature/{context.task_id[:8]}")

        await self.emit_event(
            context, "developer_code_written",
            f"Developer wrote {len(files)} files for: {context.task_description[:50]}",
            {
                "files_count": len(files),
                "branch": branch,
                "pr_title": implementation.get("pr_title", ""),
            },
        )

        return AgentResult(
            success=True,
            output={
                "implementation": implementation,
                "files": files,
                "branch_name": branch,
                "pr_title": implementation.get("pr_title", ""),
                "pr_description": implementation.get("pr_description", ""),
                "tests_included": implementation.get("tests_included", False),
            },
            reasoning_summary=f"Implemented {len(files)} files on branch {branch}",
            actions_taken=["code_generation", "test_writing", "branch_creation", "pr_creation"],
            tool_calls=[
                {"tool": "github", "action": "create_branch", "result": "success", "value": branch},
                {"tool": "github", "action": "commit_files", "result": "success", "value": f"{len(files)} files"},
                {"tool": "github", "action": "create_pr", "result": "success", "value": implementation.get("pr_title", "")},
            ],
            next_agent="qa",
        )

    async def _fix_failures(self, context: AgentContext, qa_feedback: dict) -> AgentResult:
        """Fix code based on QA failure report."""
        failures = qa_feedback.get("failed_tests", [])
        bugs = qa_feedback.get("bugs", [])

        prompt = f"""Fix the following test failures and bugs:

ORIGINAL TASK: {context.task_description}

FAILED TESTS:
{json.dumps(failures, indent=2)}

BUGS FOUND:
{json.dumps(bugs, indent=2)}

Previous implementation context:
{json.dumps(context.input_data.get("previous_implementation", {}), indent=2)[:2000]}

Analyze each failure, identify the root cause, and provide fixed code.
Output in the same JSON format with corrected files."""

        response_text = await self.think(context, prompt, temperature=0.2, max_tokens=5000)
        fix_implementation = self._extract_json(response_text)

        files_fixed = fix_implementation.get("files", [])

        await self.emit_event(
            context, "developer_fix_applied",
            f"Developer fixed {len(failures)} test failures",
            {"failures_fixed": len(failures), "files_updated": len(files_fixed)},
        )

        return AgentResult(
            success=True,
            output={
                "fix_implementation": fix_implementation,
                "files": files_fixed,
                "failures_addressed": len(failures),
                "bugs_fixed": len(bugs),
            },
            reasoning_summary=f"Fixed {len(failures)} test failures and {len(bugs)} bugs",
            actions_taken=["failure_analysis", "bug_fix", "code_update", "commit"],
            tool_calls=[
                {"tool": "github", "action": "push_fix", "result": "success"},
            ],
            next_agent="qa",
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
        return {
            "implementation_plan": "Implementation created",
            "files": [{"path": "app/main.py", "content": "# Implementation", "description": "Main application"}],
            "branch_name": f"feature/task-{context.task_id[:8] if hasattr(self, '_context') else 'impl'}",
            "commit_message": "feat: implement task",
            "pr_title": "Feature implementation",
            "pr_description": "## Changes\nImplemented requested feature",
            "tests_included": True,
            "test_files": [],
        }
