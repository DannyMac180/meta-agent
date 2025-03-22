"""
Unit tests for handling empty input in the generate_agent function.
"""

import pytest
from meta_agent.core import generate_agent


@pytest.mark.asyncio
async def test_generate_agent_empty_input():
    """Test that the generate_agent function raises an error with empty input."""
    # Now that we've added the check directly in core.py, we can test it directly
    with pytest.raises(ValueError, match="Agent specification cannot be empty"):
        await generate_agent("")
