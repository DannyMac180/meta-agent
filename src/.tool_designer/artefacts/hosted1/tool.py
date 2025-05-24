
# Always define the stub class directly
class WebSearchTool:  # pragma: no cover – stub for CI
    def __init__(self, *_a, **_kw):
        pass
    def run(self, query: str, *_a, **_kw) -> str:
        return f"Search results for (stub.run): {query}"

def search_web(query: str, tool_instance: WebSearchTool) -> str:
    """Search the web for the given query using the provided tool instance."""
    try:
        result = tool_instance.run(query)
        return result
    except Exception as e:
        raise e
