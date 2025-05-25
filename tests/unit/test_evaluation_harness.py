from unittest.mock import MagicMock

from meta_agent.evaluation.harness import EvaluationHarness
from meta_agent.evaluation.result_collection import CollectionResult


def test_init_creates_default_modules(monkeypatch):
    fake_rc_cls = MagicMock()
    fake_rc = MagicMock()
    fake_rc_cls.return_value = fake_rc
    fake_reporter_cls = MagicMock()
    fake_reporter = MagicMock()
    fake_reporter_cls.return_value = fake_reporter
    monkeypatch.setattr(
        'meta_agent.evaluation.harness.ResultCollectionModule', fake_rc_cls
    )
    monkeypatch.setattr('meta_agent.evaluation.harness.ReportingModule', fake_reporter_cls)

    harness = EvaluationHarness()
    assert harness.result_collector is fake_rc
    assert harness.reporter is fake_reporter


def test_evaluate_flow(monkeypatch, tmp_path):
    fake_rc = MagicMock()
    collection = CollectionResult(exit_code=0, stdout='out', stderr='err', duration=1.0)
    fake_rc.execute_and_collect.return_value = collection
    fake_reporter = MagicMock()
    fake_reporter.generate_report.return_value = 'REPORT'

    harness = EvaluationHarness(fake_rc, fake_reporter)
    result = harness.evaluate(tmp_path, timeout=5, output_format='json')

    assert result == 'REPORT'
    fake_rc.execute_and_collect.assert_called_with(tmp_path, timeout=5)
    fake_reporter.generate_report.assert_called_with(collection, output_format='json')


def test_evaluate_logs(monkeypatch, tmp_path, caplog):
    fake_rc = MagicMock()
    fake_rc.execute_and_collect.return_value = CollectionResult(0, '', '', 0.1)
    fake_reporter = MagicMock()
    fake_reporter.generate_report.return_value = ''
    harness = EvaluationHarness(fake_rc, fake_reporter)
    with caplog.at_level('INFO', logger='meta_agent.evaluation.harness'):
        harness.evaluate(tmp_path)
    assert any('Starting evaluation for' in r.getMessage() for r in caplog.records)
