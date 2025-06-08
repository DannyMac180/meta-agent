import logging
import click
import pytest

from meta_agent.ux import (
    CLIOutput,
    DiagramGenerator,
    ErrorHandler,
    Interactive,
    UserFeedback,
    NotificationSeverity,
    CLIOutputError,
    DiagramGenerationError,
)


@pytest.fixture
def capture_secho(monkeypatch):
    messages = []

    def fake_secho(message, **kwargs):
        messages.append(click.unstyle(message))

    monkeypatch.setattr(click, "secho", fake_secho)
    return messages


def test_basic_ux_workflow(monkeypatch, capsys, capture_secho):
    # Simulate interactive choices
    inputs = iter(["1", "foo", "bar"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    cli = CLIOutput()
    feedback = UserFeedback(cli_output=cli)
    interactive = Interactive()
    generator = DiagramGenerator()

    # interactive menu and form
    choice = interactive.menu("Select", ["diagram", "quit"])
    params = interactive.form(["a", "b"])

    assert choice == "diagram"
    assert params == {"a": "foo", "b": "bar"}

    list(feedback.progress_iter(range(2), description="progress"))
    out, err = capsys.readouterr()
    combined = click.unstyle(out + err)

    spec = {
        "task_description": "Demo",
        "inputs": {"q": "str"},
        "outputs": {"r": "str"},
    }
    diagram = generator.generate(spec)
    feedback.notify("done", NotificationSeverity.SUCCESS)

    assert "done" in capture_secho
    assert "progress" in combined
    assert diagram.startswith("flowchart")


def test_error_propagation(monkeypatch, caplog):
    def fail_secho(*args, **kwargs):
        raise OSError("boom")

    # Force CLI output to fail so CLIOutputError is raised
    monkeypatch.setattr(click, "secho", fail_secho)
    cli = CLIOutput()

    with pytest.raises(CLIOutputError) as exc:
        cli.info("hi")

    # Restore working output for error handling path
    monkeypatch.setattr(click, "secho", lambda *a, **k: None)
    handler = ErrorHandler(cli_output=cli, log=logging.getLogger("test"))
    with caplog.at_level(logging.ERROR):
        handler.handle(exc.value)
    assert "failed to write output" in caplog.text

    # Diagram generation failure should propagate through ErrorHandler
    generator = DiagramGenerator()
    with caplog.at_level(logging.ERROR):
        try:
            generator.generate(None)  # type: ignore[arg-type]
        except DiagramGenerationError as dg_err:
            handler.handle(dg_err)
    assert "spec must be a mapping" in caplog.text

    feedback = UserFeedback(cli_output=cli)
    suggestion = feedback.error_suggestion("Failed to load file")
    assert suggestion and "file path exists" in suggestion
