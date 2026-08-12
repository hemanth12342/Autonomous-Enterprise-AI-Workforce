"""
OpenAI LLM Provider — GPT-4o and embeddings.
"""
import time
from typing import Optional

from openai import AsyncOpenAI

from app.llm.provider import LLMProvider, LLMMessage, LLMResponse, calculate_cost
from app.config import settings


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4o provider with native embedding support."""

    def __init__(self):
        super().__init__(
            model=settings.openai_model,
            fast_model=settings.openai_fast_model,
        )
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

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
            provider="openai",
            cost_usd=cost,
            latency_seconds=latency,
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding
