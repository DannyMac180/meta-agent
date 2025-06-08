import logging

from meta_agent.ux import (
    CLIOutput,
    ErrorHandler,
    CLIOutputError,
    UXError,
    DiagramGenerationError,
)


def test_error_handler_logs_and_outputs(caplog, capsys):
    handler = ErrorHandler(cli_output=CLIOutput())
    err = CLIOutputError("boom", context={"foo": "bar"})
    with caplog.at_level(logging.ERROR):
        handler.handle(err)
    out, err_stream = capsys.readouterr()
    assert "boom" in err_stream
    assert "boom" in caplog.text
    assert "foo" in caplog.text


def test_diagram_generation_error_subclass():
    assert issubclass(DiagramGenerationError, UXError)
