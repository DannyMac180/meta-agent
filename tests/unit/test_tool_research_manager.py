import types
import pytest

from meta_agent.research_manager import ToolResearchManager


class DummyTool:
    def __init__(self):
        self.calls = []

    def __call__(self, query: str):
        self.calls.append(query)
        return "result line 1\nresult line 2"


def test_formulate_query():
    mgr = ToolResearchManager(web_search_tool=DummyTool(), enabled=True)
    q = mgr.formulate_query("foo", "does bar")
    assert "foo" in q and "bar" in q


def test_search_caching():
    tool = DummyTool()
    mgr = ToolResearchManager(web_search_tool=tool, enabled=True)
    r1 = mgr.research("foo", "bar")
    r2 = mgr.research("foo", "bar")
    assert r1 == ["result line 1", "result line 2"]
    assert r2 == r1
    assert len(tool.calls) == 1

