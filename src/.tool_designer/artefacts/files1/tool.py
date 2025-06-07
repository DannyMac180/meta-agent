import logging
from typing import Any

logger = logging.getLogger(__name__)

# Searches files for a term
def file_search(
    term: str,
    path: str = None
) -> list:
    """Searches files for a term"

    Args:
        term: Search term (Required)
        path: File path (Optional)

    Returns:
        list: list
    """
    logger.info(f"Running tool: file_search")
    result = None
    logger.warning('Tool logic not yet implemented!')
    return result