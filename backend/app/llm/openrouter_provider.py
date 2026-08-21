"""
OpenRouter LLM Provider — access 100+ models via a single OpenAI-compatible API.
https://openrouter.ai/docs
"""
import time
from typing import Optional

import httpx

from app.llm.provider import LLMProvider, LLMMessage, LLMResponse, calculate_cost
from app.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter provider — OpenAI-compatible API aggregating 100+ models.
    Supports models from OpenAI, Anthropic, Meta, Mistral, Google, and more.
    """

    def __init__(self):
        super().__init__(
            model=settings.openrouter_model,
            fast_model=settings.openrouter_fast_model,
        )
        self._headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
            "Content-Type": "application/json",
        }

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

        payload = {
            "model": model,
            "messages": built_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()
        latency = time.time() - start

        data = response.json()
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # OpenRouter returns cost directly in some responses
        cost_usd = data.get("usage", {}).get("cost", None)
        if cost_usd is None:
            cost_usd = calculate_cost(model, prompt_tokens, completion_tokens)

        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
        finish_reason = choice.get("finish_reason", "stop") or "stop"

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            provider="openrouter",
            cost_usd=cost_usd,
            latency_seconds=latency,
            finish_reason=finish_reason,
        )

    async def embed(self, text: str) -> list[float]:
        """
        OpenRouter does not expose an embeddings endpoint.
        Falls back to OpenAI embeddings if an OPENAI_API_KEY is available,
        otherwise raises a clear error.
        """
        if settings.openai_api_key:
            from app.llm.openai_provider import OpenAIProvider
            fallback = OpenAIProvider()
            return await fallback.embed(text)
        raise NotImplementedError(
            "OpenRouter does not support embeddings. "
            "Set OPENAI_API_KEY to use OpenAI as the embedding fallback, "
            "or switch EMBEDDING_PROVIDER to 'sentence-transformers'."
        )
