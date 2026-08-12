"""
Base Agent — all specialized agents inherit this.
Implements the OBSERVE → THINK → ACT → VERIFY → COMPLETE loop
with full audit logging, cost tracking, retry logic, and guardrails.
"""
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from app.config import settings
from app.llm.router import LLMRouter, get_llm_router, TaskComplexity
from app.llm.provider import LLMMessage
from app.memory.short_term import (
    set_agent_state, get_agent_state, publish_event, get_project_channel
)
from app.security.guardrails import guardrails, GuardrailViolation

log = structlog.get_logger(__name__)


@dataclass
class AgentContext:
    """Everything an agent needs to execute a task."""
    project_id: str
    task_id: str
    agent_type: str
    organization_id: str
    task_description: str
    input_data: dict = field(default_factory=dict)
    budget_remaining_usd: float = 1.0
    retry_count: int = 0
    demo_mode: bool = True


@dataclass
class AgentResult:
    """Structured output from an agent run."""
    success: bool
    output: dict
    reasoning_summary: str
    actions_taken: list[str]
    tool_calls: list[dict]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    requires_approval: bool = False
    approval_risk: str = "low"
    next_agent: Optional[str] = None  # suggests which agent to call next


class BaseAgent(ABC):
    """
    Abstract base for all AI agents.

    Lifecycle:
        IDLE → PLANNING → EXECUTING → VERIFYING → COMPLETED | FAILED | ESCALATED
    """

    def __init__(
        self,
        agent_type: str,
        name: str,
        description: str,
        llm_complexity: TaskComplexity = TaskComplexity.MODERATE,
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.llm_complexity = llm_complexity
        self.router: LLMRouter = get_llm_router()
        self.log = structlog.get_logger(f"agent.{agent_type}")

    # ─── Abstract Interface ───────────────────────────────────────────────────
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Agent-specific system prompt."""
        ...

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Core execution logic — to be implemented by each agent."""
        ...

    # ─── Shared Utilities ─────────────────────────────────────────────────────
    async def think(
        self,
        context: AgentContext,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Call the LLM with guardrails and cost tracking."""
        # Check prompt injection
        try:
            guardrails.check_prompt_injection(user_message)
        except GuardrailViolation as e:
            self.log.warning("Prompt injection attempt detected", reason=e.reason)
            return "I cannot process this request as it contains potentially unsafe content."

        messages = [LLMMessage(role="user", content=user_message)]

        response = await self.router.chat(
            messages=messages,
            agent_type=self.agent_type,
            complexity=self.llm_complexity,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=self.get_system_prompt(),
        )

        # Track cost deduction from budget
        context.budget_remaining_usd -= response.cost_usd

        return response.content

    async def emit_event(self, context: AgentContext, event_type: str, message: str, data: dict = None) -> None:
        """Broadcast a real-time event to the WebSocket channel."""
        event = {
            "event_type": event_type,
            "agent_type": self.agent_type,
            "agent_name": self.name,
            "project_id": context.project_id,
            "task_id": context.task_id,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            channel = await get_project_channel(context.project_id)
            await publish_event(channel, event)
            # Also publish to global channel
            await publish_event("global:events", event)
        except Exception as e:
            self.log.warning("Failed to publish event", error=str(e))

    async def save_state(self, context: AgentContext, state: dict) -> None:
        """Persist agent state to Redis."""
        await set_agent_state(self.agent_type, context.project_id, {
            **state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    async def load_state(self, context: AgentContext) -> Optional[dict]:
        """Load agent state from Redis."""
        return await get_agent_state(self.agent_type, context.project_id)

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Entry point — runs execute() with retry logic, timing, and error handling.
        """
        start = time.time()
        self.log.info(
            "Agent starting",
            agent=self.agent_type,
            project=context.project_id,
            task=context.task_id,
            retry=context.retry_count,
        )

        await self.emit_event(context, "agent_started", f"{self.name} started task")

        for attempt in range(1, settings.max_agent_retries + 1):
            try:
                result = await self.execute(context)
                result.duration_seconds = time.time() - start

                if result.success:
                    await self.emit_event(
                        context, "agent_completed",
                        f"{self.name} completed successfully",
                        {"cost_usd": result.cost_usd},
                    )
                else:
                    await self.emit_event(
                        context, "agent_failed",
                        f"{self.name} failed: {result.error_message}",
                    )

                self.log.info(
                    "Agent finished",
                    agent=self.agent_type,
                    success=result.success,
                    cost=result.cost_usd,
                    duration=result.duration_seconds,
                )
                return result

            except GuardrailViolation as gv:
                self.log.error("Guardrail violation", reason=gv.reason, severity=gv.severity)
                await self.emit_event(context, "guardrail_violation", f"Blocked: {gv.reason}")
                return AgentResult(
                    success=False,
                    output={},
                    reasoning_summary=f"Guardrail blocked: {gv.reason}",
                    actions_taken=["guardrail_check"],
                    tool_calls=[],
                    error_message=str(gv),
                    duration_seconds=time.time() - start,
                )

            except Exception as e:
                self.log.error("Agent error", attempt=attempt, error=str(e))
                if attempt < settings.max_agent_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    context.retry_count += 1
                    continue
                else:
                    await self.emit_event(context, "agent_escalated", f"{self.name} requires intervention")
                    return AgentResult(
                        success=False,
                        output={},
                        reasoning_summary=f"Failed after {attempt} attempts",
                        actions_taken=[],
                        tool_calls=[],
                        error_message=str(e),
                        duration_seconds=time.time() - start,
                    )

        # Should never reach here
        return AgentResult(
            success=False,
            output={},
            reasoning_summary="Exceeded retry limit",
            actions_taken=[],
            tool_calls=[],
            duration_seconds=time.time() - start,
        )
