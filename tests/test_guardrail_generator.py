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


def test_guardrail_config_from_dict():
    data = {"rules": [{"name": "pii", "pattern": "ssn"}]}
    cfg = GuardrailConfig.from_dict(data)
    assert len(cfg.rules) == 1
    assert cfg.rules[0].name == "pii"


@pytest.mark.asyncio
async def test_build_regex_guardrails_multiple_rules():
    cfg = GuardrailConfig(
        rules=[
            GuardrailRule(name="a", pattern="foo"),
            GuardrailRule(name="b", pattern="bar"),
        ]
    )
    guards = build_regex_guardrails(cfg)
    assert len(guards) == 2

    await guards[0]("nothing here")
    await guards[1]("nothing here")

    with pytest.raises(ValueError):
        await guards[0]("foo")
    with pytest.raises(ValueError):
        await guards[1]("bar")
