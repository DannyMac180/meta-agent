"""Prototype Guardrail Designer agent with model routing."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional


class AgentBase:
    """Minimal base class used when the Agents SDK is unavailable."""

    def __init__(self, name: str | None = None, *_, **__):
        self.name = name or "StubAgent"

    async def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"status": "error", "error": "agents SDK unavailable"}


from meta_agent.services.guardrail_router import GuardrailModelRouter, LLMModelAdapter
from meta_agent.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class GuardrailDesignerAgent(AgentBase):
    """Generates guardrail code using configurable model backends."""

    def __init__(
        self,
        model_router: Optional[GuardrailModelRouter] = None,
        *,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o",
    ) -> None:
        super().__init__(name="GuardrailDesignerAgent", tools=[])

        if model_router is None:
            service = LLMService(api_key=api_key, model=default_model)
            adapter = LLMModelAdapter(service)
            model_router = GuardrailModelRouter({default_model: adapter}, default_model)
        self.model_router = model_router
        self.default_model = default_model
        logger.info("GuardrailDesignerAgent initialized with model %s", default_model)

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        prompt = specification.get("prompt") or specification.get("description", "")
        model = specification.get("model", self.default_model)
        result = await self.model_router.invoke(prompt, model=model)
        return {"status": "success", "output": result}
