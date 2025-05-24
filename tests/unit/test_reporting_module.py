from meta_agent.evaluation.reporting import ReportingModule, SummaryReport
from meta_agent.evaluation.result_collection import CollectionResult


def make_result(exit_code: int = 0) -> CollectionResult:
    return CollectionResult(exit_code=exit_code, stdout="out", stderr="err", duration=1.23)


def test_summarize_creates_report():
    module = ReportingModule()
    result = make_result()
    report = module.summarize(result)
    assert isinstance(report, SummaryReport)
    assert report.exit_code == 0
    assert report.passed is True
    assert report.duration == 1.23
    assert report.stdout == "out"
    assert report.stderr == "err"


def test_generate_json_report():
    module = ReportingModule()
    result = make_result(exit_code=1)
    json_report = module.generate_report(result, output_format="json")
    assert "\"exit_code\": 1" in json_report
    assert "\"passed\": false" in json_report


def test_generate_html_report():
    module = ReportingModule()
    result = make_result()
    html_report = module.generate_report(result, output_format="html")
    assert html_report.startswith("<html>")
    assert "PASSED" in html_report

