"""
Services package for meta_agent.

This package contains service classes that interface with external APIs
and provide functionality to other components of the meta_agent system.
"""

try:  # Optional dependency imports may fail in test environments
    from .llm_service import LLMService
except Exception:  # pragma: no cover - fallback when optional deps missing
    LLMService = None  # type: ignore[misc]

try:
    from .guardrail_router import GuardrailModelRouter, ModelAdapter, LLMModelAdapter
except Exception:  # pragma: no cover - fallback when optional deps missing
    GuardrailModelRouter = ModelAdapter = LLMModelAdapter = None  # type: ignore[misc]

from .telemetry_client import TelemetryAPIClient, EndpointConfig

__all__ = [
    "LLMService",
    "GuardrailModelRouter",
    "ModelAdapter",
    "LLMModelAdapter",
    "TelemetryAPIClient",
    "EndpointConfig",
]
