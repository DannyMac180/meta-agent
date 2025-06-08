import pytest
from meta_agent.ux import Interactive, InteractiveError


def test_ask(monkeypatch):
    inter = Interactive()
    monkeypatch.setattr("builtins.input", lambda _: "answer")
    assert inter.ask("Question?") == "answer"


def test_menu(monkeypatch, capsys):
    inputs = iter(["3", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    inter = Interactive()
    result = inter.menu("Pick one", ["a", "b"])
    out = capsys.readouterr().out
    assert "Invalid choice" in out
    assert result == "b"


def test_form(monkeypatch):
    inputs = iter(["foo", "bar"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    inter = Interactive()
    result = inter.form(["first", "second"])
    assert result == {"first": "foo", "second": "bar"}


def test_menu_empty_options():
    inter = Interactive()
    with pytest.raises(InteractiveError):
        inter.menu("Pick", [])


def test_ask_interrupt(monkeypatch):
    def raise_interrupt(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_interrupt)
    inter = Interactive()
    with pytest.raises(InteractiveError):
        inter.ask("Question")
