import logging
from typing import Any

logger = logging.getLogger(__name__)

# Adds two numbers together
def add_numbers(
    a: int,
    b: int
) -> int:
    """Adds two numbers together"

    Args:
        a: First number (Required)
        b: Second number (Required)

    Returns:
        int: int
    """
    logger.info(f'Running tool: add_numbers')
    result = None
    logger.warning('Tool logic not yet implemented!')
    return result