"""
LLM Provider abstraction — swap providers via environment variables.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import time


@dataclass
class LLMResponse:
    """Standardized LLM response across all providers."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: str
    cost_usd: float
    latency_seconds: float
    finish_reason: str = "stop"


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


# ─── Cost tables (USD per 1M tokens) ─────────────────────────────────────────
COST_TABLE: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o":             {"prompt": 2.50,  "completion": 10.00},
    "gpt-4o-mini":        {"prompt": 0.15,  "completion": 0.60},
    "gpt-4-turbo":        {"prompt": 10.00, "completion": 30.00},
    # Groq
    "llama-3.3-70b-versatile": {"prompt": 0.59, "completion": 0.79},
    "llama-3.1-8b-instant":    {"prompt": 0.05, "completion": 0.08},
    "mixtral-8x7b-32768":      {"prompt": 0.24, "completion": 0.24},
    # Azure (same as OpenAI)
    "gpt-4o-azure":       {"prompt": 2.50,  "completion": 10.00},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost in USD."""
    rates = COST_TABLE.get(model, {"prompt": 1.0, "completion": 2.0})
    return (prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]) / 1_000_000


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, model: str, fast_model: str):
        self.model = model
        self.fast_model = fast_model

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_fast_model: bool = False,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Send chat messages and return a structured response."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for a text."""
        ...

    def _build_messages(
        self, messages: list[LLMMessage], system_prompt: Optional[str]
    ) -> list[dict]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        result.extend({"role": m.role, "content": m.content} for m in messages)
        return result
