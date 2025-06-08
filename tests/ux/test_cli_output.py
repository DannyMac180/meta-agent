import click
from meta_agent.ux import CLIOutput


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
