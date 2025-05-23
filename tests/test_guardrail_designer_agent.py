import pytest

from meta_agent.agents.guardrail_designer_agent import GuardrailDesignerAgent
from meta_agent.services.guardrail_router import GuardrailModelRouter


class DummyAdapter:
    async def invoke(self, prompt: str, context=None) -> str:
        return f"{prompt}:guarded"


@pytest.mark.asyncio
async def test_agent_routes_prompt_through_router():
    adapter = DummyAdapter()
    router = GuardrailModelRouter({"gpt": adapter}, default_model="gpt")
    agent = GuardrailDesignerAgent(model_router=router)

    result = await agent.run({"prompt": "hello"})

    assert result["status"] == "success"
    assert result["output"] == "hello:guarded"


def test_agent_creates_default_router(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    agent = GuardrailDesignerAgent()
    assert isinstance(agent.model_router, GuardrailModelRouter)
    assert agent.default_model == agent.model_router.default_model
