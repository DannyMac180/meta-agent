from typing import List
import logging
try:
    from agents import WebSearchTool, FileSearchTool  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    logging.warning("Hosted tools unavailable: using stub implementations for WebSearchTool, FileSearchTool.")
    def _stub_func(*a, **kw):
        return "Hosted tool unavailable in this environment."
    WebSearchTool = _stub_func  # type: ignore
    FileSearchTool = _stub_func  # type: ignore

def search_docs(query: str, k: int = 3) -> List[str]:
    """
    Search for documentation or API references using WebSearchTool.
    Returns a list of top-k relevant snippets.
    """
    results = WebSearchTool(query)
    # Just a stub: if results is a string, split into lines/snippets
    if isinstance(results, str):
        snippets = [line.strip() for line in results.split('\n') if line.strip()]
        return snippets[:k]
    # If results is a list/dict, adapt as needed
    return results[:k] if isinstance(results, list) else [str(results)]
