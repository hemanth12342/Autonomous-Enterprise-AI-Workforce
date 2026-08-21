"""
LLM Router — intelligent model selection based on task complexity.
Routes tasks to the most cost-effective model that can handle them.
"""
from enum import Enum
from functools import lru_cache
from typing import Optional

from app.config import settings
from app.llm.provider import LLMProvider, LLMMessage, LLMResponse


class TaskComplexity(str, Enum):
    """Complexity classification for model routing."""
    SIMPLE = "simple"          # Classification, summarization, short answers
    MODERATE = "moderate"      # Standard generation, explanations
    COMPLEX = "complex"        # Architecture, security analysis, multi-step reasoning
    CODE = "code"              # Code generation and review
    CRITICAL = "critical"      # Security-critical, high-stakes decisions


# ─── Routing table ────────────────────────────────────────────────────────────
# Maps (provider, complexity) → whether to use fast_model
FAST_MODEL_ROUTING: dict[TaskComplexity, bool] = {
    TaskComplexity.SIMPLE:   True,   # Use fast/cheap model
    TaskComplexity.MODERATE: False,  # Use primary model
    TaskComplexity.COMPLEX:  False,  # Use primary model
    TaskComplexity.CODE:     False,  # Use primary model
    TaskComplexity.CRITICAL: False,  # Always use primary model
}

# Agent type → preferred task complexity
AGENT_COMPLEXITY_MAP: dict[str, TaskComplexity] = {
    "ceo":              TaskComplexity.COMPLEX,
    "project_manager":  TaskComplexity.MODERATE,
    "developer":        TaskComplexity.CODE,
    "qa":               TaskComplexity.MODERATE,
    "devops":           TaskComplexity.MODERATE,
    "security":         TaskComplexity.CRITICAL,
    "documentation":    TaskComplexity.SIMPLE,
    "support":          TaskComplexity.SIMPLE,
    "research":         TaskComplexity.MODERATE,
}


@lru_cache
def get_provider() -> LLMProvider:
    """Return the configured LLM provider (singleton)."""
    provider_name = settings.llm_provider
    if provider_name == "groq":
        from app.llm.groq_provider import GroqProvider
        return GroqProvider()
    elif provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "azure":
        from app.llm.openai_provider import OpenAIProvider  # Azure uses OpenAI-compatible API
        return OpenAIProvider()
    elif provider_name == "openrouter":
        from app.llm.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider()
    else:
        # Default fallback to OpenRouter
        from app.llm.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider()


class LLMRouter:
    """
    Intelligent LLM router. Selects the appropriate model based on:
    - Agent type
    - Task complexity
    - Cost budget remaining
    - Provider availability
    """

    def __init__(self):
        self.provider = get_provider()

    async def chat(
        self,
        messages: list[LLMMessage],
        agent_type: Optional[str] = None,
        complexity: Optional[TaskComplexity] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        # Determine complexity from agent type if not provided
        if complexity is None and agent_type:
            complexity = AGENT_COMPLEXITY_MAP.get(agent_type, TaskComplexity.MODERATE)
        elif complexity is None:
            complexity = TaskComplexity.MODERATE

        # Route to fast or primary model
        use_fast = FAST_MODEL_ROUTING.get(complexity, False)

        return await self.provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            use_fast_model=use_fast,
            system_prompt=system_prompt,
        )

    async def embed(self, text: str) -> list[float]:
        return await self.provider.embed(text)


# ─── Global singleton ──────────────────────────────────────────────────────────
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
