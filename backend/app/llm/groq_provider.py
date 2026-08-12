"""
Groq LLM Provider — fast, cost-effective inference.
"""
import time
from typing import Optional

from groq import AsyncGroq

from app.llm.provider import LLMProvider, LLMMessage, LLMResponse, calculate_cost
from app.config import settings


class GroqProvider(LLMProvider):
    """Groq inference — Llama/Mixtral models with very low latency."""

    def __init__(self):
        super().__init__(
            model=settings.groq_model,
            fast_model=settings.groq_fast_model,
        )
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_fast_model: bool = False,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        model = self.fast_model if use_fast_model else self.model
        built_messages = self._build_messages(messages, system_prompt)

        start = time.time()
        response = await self.client.chat.completions.create(
            model=model,
            messages=built_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.time() - start

        usage = response.usage
        cost = calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)

        return LLMResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            model=model,
            provider="groq",
            cost_usd=cost,
            latency_seconds=latency,
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    async def embed(self, text: str) -> list[float]:
        # Groq doesn't support embeddings natively — use OpenAI fallback
        from app.llm.openai_provider import OpenAIProvider
        fallback = OpenAIProvider()
        return await fallback.embed(text)
