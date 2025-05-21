import logging
from typing import Callable, Dict, List, Optional

try:
    from agents import WebSearchTool
except (ImportError, AttributeError):
    logging.warning(
        "Hosted tools unavailable: using stub WebSearchTool implementation."
    )

    class _StubWebSearchTool:  # pylint: disable=too-few-public-methods
        def __call__(self, *_, **__):  # noqa: D401
            return "Hosted tool unavailable in this environment."

    WebSearchTool = _StubWebSearchTool()  # type: ignore

logger = logging.getLogger(__name__)


class ToolResearchManager:
    """Simple manager for performing web searches related to a tool spec."""

    def __init__(
        self,
        web_search_tool: Optional[Callable[[str], str]] = None,
        enabled: bool = True,
        max_results: int = 3,
    ) -> None:
        self.web_search_tool = web_search_tool or WebSearchTool()
        self.enabled = enabled
        self.max_results = max_results
        self.cache: Dict[str, List[str]] = {}

    def formulate_query(self, name: str, purpose: str) -> str:
        """Create a simple search query from tool name and purpose."""
        query = f"{name} {purpose} examples"
        logger.debug("Formulated search query: %s", query)
        return query

    def research(self, name: str, purpose: str) -> List[str]:
        """Perform the search and return a list of result snippets."""
        if not self.enabled:
            logger.debug("Research disabled; skipping web search")
            return []

        query = self.formulate_query(name, purpose)
        if query in self.cache:
            logger.debug("Using cached results for query: %s", query)
            return self.cache[query]

        try:
            raw = self.web_search_tool(query)
            if isinstance(raw, str):
                snippets = [s.strip() for s in raw.split("\n") if s.strip()]
            elif isinstance(raw, list):
                snippets = [str(s) for s in raw]
            else:
                snippets = [str(raw)]

            snippets = snippets[: self.max_results]
            self.cache[query] = snippets
            logger.info("Collected %d research snippets", len(snippets))
            return snippets
        except Exception as exc:  # pragma: no cover - shouldn't happen in tests
            logger.error("Web search failed: %s", exc)
            return []

