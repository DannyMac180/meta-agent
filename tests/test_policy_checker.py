import pytest

from meta_agent.policy import PolicyChecker
from meta_agent.generators.guardrail_generator import (
    GuardrailConfig,
    GuardrailRule,
    GuardrailAction,
)


@pytest.mark.asyncio
async def test_policy_checker_deny():
    config = GuardrailConfig(rules=[GuardrailRule(name="block", pattern="bad")])
    checker = PolicyChecker(config)

    await checker.run("good text")  # should pass

    with pytest.raises(ValueError):
        await checker.run("bad text")


@pytest.mark.asyncio
async def test_policy_checker_redact():
    config = GuardrailConfig(
        rules=[
            GuardrailRule(
                name="secret", pattern="secret", action=GuardrailAction.REDACT
            )
        ]
    )
    checker = PolicyChecker(config)

    result = await checker.run("my secret is here")
    assert result == "my [REDACTED] is here"


@pytest.mark.asyncio
async def test_policy_checker_custom_plugin():
    checker = PolicyChecker()

    async def plugin(text: str) -> str:
        return text.upper()

    checker.add_check(plugin)

    result = await checker.run("hello")
    assert result == "HELLO"
