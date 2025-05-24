from tool import search_web, WebSearchTool

def test_search_web():
    test_tool_instance = WebSearchTool()
    result = search_web("openai agents sdk", tool_instance=test_tool_instance)
    assert isinstance(result, str)
    assert "(stub.run): openai agents sdk" in result
