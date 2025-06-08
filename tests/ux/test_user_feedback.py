import sys
import click

from meta_agent.ux import UserFeedback, NotificationSeverity


def test_progress_iter(capsys):
    fb = UserFeedback()
    items = [1, 2, 3]
    result = list(fb.progress_iter(items, description="doing"))
    out, err = capsys.readouterr()
    assert result == items
    assert "doing" in click.unstyle(out + err)


def test_notify_levels(capsys):
    fb = UserFeedback()
    fb.notify("ok", NotificationSeverity.SUCCESS)
    out, _ = capsys.readouterr()
    assert "ok" in click.unstyle(out)


def test_error_suggestion(capsys):
    fb = UserFeedback()
    suggestion = fb.error_suggestion("Failed to load file")
    out, _ = capsys.readouterr()
    assert suggestion is not None
    assert "file path exists" in suggestion
    assert "Suggestion" in click.unstyle(out)


def test_copy_to_clipboard(monkeypatch):
    copied = {}

    class Dummy:
        def copy(self, text):
            copied["text"] = text

    monkeypatch.setitem(sys.modules, "pyperclip", Dummy())
    fb = UserFeedback()
    assert fb.copy_to_clipboard("hello")
    assert copied["text"] == "hello"
