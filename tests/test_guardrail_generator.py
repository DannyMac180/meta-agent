import pytest

from meta_agent.generators.guardrail_generator import (
    GuardrailAction,
    GuardrailRule,
    GuardrailConfig,
    build_regex_guardrails,
)


def test_guardrail_rule_validation():
    rule = GuardrailRule(name="no-secrets", pattern=r"secret")
    assert rule.action is GuardrailAction.DENY

    with pytest.raises(ValueError):
        GuardrailRule(name="bad", pattern="(")


def test_guardrail_config_add_rule():
    config = GuardrailConfig()
    rule = GuardrailRule(name="block", pattern="bad")
    config.add_rule(rule)
    assert config.rules == [rule]


@pytest.mark.asyncio
async def test_build_regex_guardrails_trigger():
    config = GuardrailConfig(rules=[GuardrailRule(name="block", pattern="bad")])
    guards = build_regex_guardrails(config)
    assert len(guards) == 1
    guard = guards[0]

    await guard("good text")  # should not raise

    with pytest.raises(ValueError):
        await guard("this is bad")
