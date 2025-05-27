import pytest
from meta_agent.telemetry import TelemetryCollector


def test_usage_accumulation():
    t = TelemetryCollector(cost_cap=1.0)
    t.add_usage(500, 500, model="o3")
    assert t.token_count == 1000
    assert pytest.approx(t.cost, 0.0001) == 0.01


def test_cost_cap_enforced():
    t = TelemetryCollector(cost_cap=0.001)
    with pytest.raises(RuntimeError):
        t.add_usage(1000, 0, model="o3")


def test_summary_line():
    t = TelemetryCollector()
    t.start_timer()
    t.stop_timer()
    line = t.summary_line()
    assert "Telemetry:" in line
    assert "cost=$" in line
    assert "tokens=0" in line
