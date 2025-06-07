from meta_agent.utils.golden_specs import load_golden_spec_fuzz_set


def test_load_golden_specs() -> None:
    specs = load_golden_spec_fuzz_set()
    assert len(specs) >= 20
    assert all(isinstance(s, str) and s for s in specs)
