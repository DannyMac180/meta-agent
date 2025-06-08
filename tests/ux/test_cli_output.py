import click
import pytest
from meta_agent.ux import CLIOutput, CLIOutputError


def test_info_output(capsys):
    cli = CLIOutput()
    cli.info("hello")
    out, err = capsys.readouterr()
    assert "hello" in click.unstyle(out)
    assert err == ""


def test_verbosity_levels(capsys):
    cli = CLIOutput(verbosity=0)
    cli.info("quiet")
    out, err = capsys.readouterr()
    assert out == "" and err == ""
    cli.info("force", level=0)
    out, _ = capsys.readouterr()
    assert "force" in click.unstyle(out)


def test_error_output_stderr(capsys):
    cli = CLIOutput()
    cli.error("oops")
    out, err = capsys.readouterr()
    assert out == ""
    assert "oops" in click.unstyle(err)


def test_cli_output_error(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(click, "secho", fail)
    cli = CLIOutput()
    with pytest.raises(CLIOutputError):
        cli.info("hello")
