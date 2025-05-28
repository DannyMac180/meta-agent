import logging
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


def test_cost_cap_threshold_events(caplog):
    t = TelemetryCollector(cost_cap=0.02)
    with caplog.at_level(logging.INFO):
        t.add_usage(1000, 0, model="o3")
        assert len(t.events) == 0
        t.add_usage(500, 0, model="o3")
        assert len(t.events) == 1
        assert t.events[0].severity == TelemetryCollector.Severity.WARNING
        t.add_usage(300, 0, model="o3")
        assert len(t.events) == 2
        assert t.events[1].severity == TelemetryCollector.Severity.ERROR
        with pytest.raises(RuntimeError):
            t.add_usage(200, 0, model="o3")
        assert len(t.events) == 3
        assert t.events[-1].severity == TelemetryCollector.Severity.CRITICAL


def test_record_event():
    t = TelemetryCollector()
    t.record_event(
        TelemetryCollector.Category.EXECUTION,
        "failed",
        severity=TelemetryCollector.Severity.ERROR,
    )
    assert len(t.events) == 1
    ev = t.events[0]
    assert ev.category == TelemetryCollector.Category.EXECUTION
    assert ev.severity == TelemetryCollector.Severity.ERROR


def test_guardrail_event():
    t = TelemetryCollector()
    t.increment_guardrail_hits()
    assert t.guardrail_hits == 1
    assert len(t.events) == 1
    ev = t.events[0]
    assert ev.category == TelemetryCollector.Category.GUARDRAIL
    assert ev.severity == TelemetryCollector.Severity.WARNING
