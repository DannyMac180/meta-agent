"""Routing layer that applies guardrails before hitting the underlying model."""

from __future__ import annotations

from typing import Protocol, Dict, Any, Callable, Awaitable, Optional, List

from meta_agent.services.llm_service import LLMService


class ModelAdapter(Protocol):
    """Interface for model backends."""

    async def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] | None = None
    ) -> str:
        """Generate a response for the given prompt."""
        ...


class GuardrailModelRouter:
    """Routes requests through guardrails to a selected model adapter."""

    def __init__(self, adapters: Dict[str, ModelAdapter], default_model: str) -> None:
        if not adapters:
            raise ValueError("At least one model adapter must be provided")
        if default_model not in adapters:
            raise ValueError("Default model must exist in adapters")
        self.adapters = adapters
        self.default_model = default_model
        self.input_guardrails: List[Callable[[str], Awaitable[None]]] = []
        self.output_guardrails: List[Callable[[str], Awaitable[None]]] = []

    def add_input_guardrail(self, guardrail: Callable[[str], Awaitable[None]]) -> None:
        self.input_guardrails.append(guardrail)

    def add_output_guardrail(self, guardrail: Callable[[str], Awaitable[None]]) -> None:
        self.output_guardrails.append(guardrail)

    async def invoke(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        for guard in self.input_guardrails:
            await guard(prompt)

        adapter = self.adapters.get(model or self.default_model)
        if adapter is None:
            raise ValueError(f"Unknown model '{model}'")

        result = await adapter.invoke(prompt, context)

        for guard in self.output_guardrails:
            await guard(result)

        return result


class LLMModelAdapter:
    """Simple adapter around :class:`LLMService`."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] | None = None
    ) -> str:
        return await self.llm_service.generate_code(prompt, context or {})
