"""
Services package for meta_agent.

This package contains service classes that interface with external APIs
and provide functionality to other components of the meta_agent system.
"""

try:  # pragma: no cover - optional dependency imports
    from .llm_service import LLMService
except Exception:  # pragma: no cover - allow import without extras
    LLMService = None  # type: ignore[assignment]

try:
    from .guardrail_router import GuardrailModelRouter, ModelAdapter, LLMModelAdapter
except Exception:  # pragma: no cover - allow missing deps during minimal usage
    GuardrailModelRouter = ModelAdapter = LLMModelAdapter = None  # type: ignore

from .telemetry_client import TelemetryAPIClient, EndpointConfig

__all__ = [
    "LLMService",
    "GuardrailModelRouter",
    "ModelAdapter",
    "LLMModelAdapter",
    "TelemetryAPIClient",
    "EndpointConfig",
]
