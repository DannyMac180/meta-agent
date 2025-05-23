import re
from meta_agent.generators.regex_patterns import (
    DEFAULT_REGEX_PATTERNS,
    build_default_regex_config,
)
from meta_agent.generators.guardrail_generator import GuardrailRule


def test_default_patterns_match_samples():
    samples = {
        "email": "user@example.com",
        "phone": "+1 555-123-4567",
        "ssn": "123-45-6789",
        "credit_card": "4111 1111 1111 1111",
        "password": "my password is secret",
    }
    for name, pattern in DEFAULT_REGEX_PATTERNS.items():
        assert re.search(pattern, samples[name])


def test_build_default_regex_config():
    config = build_default_regex_config()
    rule_names = {rule.name for rule in config.rules}
    assert set(DEFAULT_REGEX_PATTERNS.keys()) == rule_names
    # ensure patterns are preserved
    for rule in config.rules:
        assert isinstance(rule, GuardrailRule)
        assert DEFAULT_REGEX_PATTERNS[rule.name] == rule.pattern
