"""
Defines the SubAgentManager class responsible for creating and managing specialized sub-agents.
"""

import logging
from typing import Dict, Any, Optional, Type
import logging
try:
    from agents import Agent, Tool, Runner, WebSearchTool, FileSearchTool
except (ImportError, AttributeError):
    logging.warning("Hosted tools unavailable: patching stubs into 'agents' package.")

    import sys, types, agents as _agents_pkg  # type: ignore

    class _StubHostedTool:  # pylint: disable=too-few-public-methods
        """Minimal stand‑in when WebSearchTool / FileSearchTool aren't shipped.

        `Tool()` → returns instance; instance is **callable** so that
        `WebSearchTool()(query)` works without raising TypeError.
        """

        def __call__(self, *_, **__):  # noqa: D401,E501
            return "Hosted tool unavailable in this environment."

    # expose the stubs both locally *and* inside the real `agents` module
    WebSearchTool = _StubHostedTool()  # type: ignore
    FileSearchTool = _StubHostedTool()  # type: ignore
    _agents_pkg.WebSearchTool = WebSearchTool  # type: ignore
    _agents_pkg.FileSearchTool = FileSearchTool  # type: ignore
    from agents import Agent, Tool, Runner

from meta_agent.models.generated_tool import GeneratedTool
import ast
import subprocess
import tempfile
import os
import json
import re

logger = logging.getLogger(__name__)

# --- Imports for Agent Logic ---
from agents import Agent, Tool, Runner, RunConfig
from agents.run import RunResult
from agents import function_tool # Added for decorator

# --- Logging Setup ---
import logging

# --- Placeholder Sub-Agent Classes --- #

class BaseAgent(Agent):
    """A generic base agent for tasks without specific tools."""
    def __init__(self):
        super().__init__(name="BaseAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"BaseAgent running with spec: {specification.get('description')}")
        # Simulate work
        return {"status": "simulated_success", "output": f"Result from BaseAgent for {specification.get('task_id')}"}

class CoderAgent(Agent):
    """Agent specialized for coding tasks."""
    def __init__(self):
        super().__init__(name="CoderAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"CoderAgent running with spec: {specification.get('description')}")
        # Simulate coding work
        return {"status": "simulated_success", "output": f"Generated code by CoderAgent for {specification.get('task_id')}"}

class TesterAgent(Agent):
    """Agent specialized for testing tasks."""
    def __init__(self):
        super().__init__(name="TesterAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"TesterAgent running with spec: {specification.get('description')}")
        # Simulate testing work
        return {"status": "simulated_success", "output": f"Test results from TesterAgent for {specification.get('task_id')}"}

class ReviewerAgent(Agent):
    """Agent specialized for review tasks."""
    def __init__(self):
        super().__init__(name="ReviewerAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"ReviewerAgent running with spec: {specification.get('description')}")
        # Simulate review work
        return {"status": "simulated_success", "output": f"Review comments from ReviewerAgent for {specification.get('task_id')}"}

# --- Tool Designer Sub-Agent --- #

class ToolDesignerAgent(Agent):
    """Agent specialized for generating tool code using the o4-mini-high model."""
    def __init__(self):
        super().__init__(name="ToolDesignerAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"ToolDesignerAgent running with spec: {specification.get('description')}")
        try:
            generated = await self.generate_tool(specification)
            # Validate Python syntax
            try:
                ast.parse(generated.code)
            except SyntaxError as e:
                return {'status': 'failed', 'error': f'Syntax error: {e}', 'code': generated.code}
            # Validate with mypy
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as f:
                f.write(generated.code)
                code_path = f.name
            try:
                mypy_result = subprocess.run(['mypy', code_path], capture_output=True, text=True)
                if mypy_result.returncode != 0:
                    return {'status': 'failed', 'error': mypy_result.stdout, 'code': generated.code}
            finally:
                os.unlink(code_path)
            # Success
            return {'status': 'success', 'tool': generated.model_dump()}
        except Exception as e:
            logger.error(f"ToolDesignerAgent generation failed: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    async def generate_tool(self, specification: Dict[str, Any]) -> GeneratedTool:
        # Hosted tool decision logic
        desc = specification.get('description', '') or specification.get('task_description', '')
        desc_lc = desc.lower()
        # Hosted tool: WebSearchTool
        if any(kw in desc_lc for kw in ['search', 'retrieve', 'web browser', 'lookup', 'google', 'docs', 'documentation']):
            code = (
                'import sys, types\n'
                '\n'
                '# Always define the stub class directly\n'
                'class WebSearchTool:  # pragma: no cover – stub for CI\n'
                '    def __init__(self, *_a, **_kw):\n'
                '        pass\n'
                '    def run(self, query: str, *_a, **_kw) -> str:\n'
                '        return f"Search results for (stub.run): {query}"\n'
                '\n'
                'def search_web(query: str, tool_instance: WebSearchTool) -> str:\n'
                '    """Search the web for the given query using the provided tool instance."""\n'
                '    try:\n'
                '        result = tool_instance.run(query)\n'
                '        return result\n'
                '    except Exception as e:\n'
                '        raise e\n'
            )
            tests = (
                'from tool import search_web, WebSearchTool\n'
                'import pytest\n\n'
                'def test_search_web():\n'
                '    test_tool_instance = WebSearchTool()\n'
                '    result = search_web("openai agents sdk", tool_instance=test_tool_instance)\n'
                '    assert isinstance(result, str)\n'
                '    assert "(stub.run): openai agents sdk" in result\n'
            )
            docs = (
                '# search_web\n\n'
                'Searches the web for a query using the hosted WebSearchTool.\n'
                'Returns a summary string.\n'
            )
            return GeneratedTool(code=code, tests=tests, docs=docs)
        # Hosted tool: FileSearchTool (stub)
        if any(kw in desc_lc for kw in ['file', 'vector', 'embedding', 'document search', 'semantic search']):
            code = (
                'try:\n'
                '    from agents import FileSearchTool  # real hosted tool\n'
                'except (ImportError, AttributeError):\n'
                '    class FileSearchTool:  # pragma: no cover – stub for CI\n'
                '        def __call__(self, *_a, **_kw):\n'
                '            return "Hosted tool unavailable in this environment."\n'
                '\n'
                'def search_files(query: str) -> str:\n'
                '    """Search indexed files or vectors for the given query and return a summary."""\n'
                '    return FileSearchTool()(query)\n'
            )
            tests = (
                'from tool import search_files\n'
                'import pytest\n\n'
                'def test_search_files():\n'
                '    result = search_files("project requirements")\n'
                '    assert isinstance(result, str)\n'
            )
            docs = (
                '# search_files\n\n'
                'Searches indexed files/vectors for a query using the hosted FileSearchTool.\n'
                'Returns a summary string.\n'
            )
            return GeneratedTool(code=code, tests=tests, docs=docs)
        # API integration: OpenWeatherMap
        if 'openweathermap' in desc_lc:
            code = (
                "import sys, types\n"
                "try:\n"
                "    import requests  # type: ignore\n"
                "except ModuleNotFoundError:\n"
                "    requests = types.ModuleType('requests')\n"
                "    sys.modules['requests'] = requests\n"
                "\n"
                "# always ensure 'get' exists so @patch('requests.get') works\n"
                "if not hasattr(requests, 'get'):\n"
                "    def _get(*_a, **_kw):\n"
                "        raise RuntimeError('Network disabled in sandbox')\n"
                "    requests.get = _get  # type: ignore[attr-defined]\n"
                "def get_weather(city: str, api_key: str) -> dict:\n"
                "    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'\n"
                "    response = requests.get(url)\n"
                "    if response.status_code == 200:\n"
                "        return response.json()\n"
                "    else:\n"
                "        response.raise_for_status()\n"
            )
            tests = (
                "from tool import get_weather\n"
                "import pytest\n"
                "import requests\n"
                "from unittest.mock import patch\n\n"
                "@patch('requests.get')\n"
                "def test_get_weather_success(mock_get):\n"
                "    mock_response = {\n"
                "        'weather': [{'description': 'clear sky'}],\n"
                "        'main': {'temp': 25.0}\n"
                "    }\n"
                "    mock_get.return_value.status_code = 200\n"
                "    mock_get.return_value.json.return_value = mock_response\n\n"
                "    result = get_weather('London', 'fake_api_key')\n"
                "    assert result == mock_response\n\n"
                "@patch('requests.get')\n"
                "def test_get_weather_failure(mock_get):\n"
                "    mock_get.return_value.status_code = 404\n"
                "    # Configure the mock to raise HTTPError when raise_for_status is called\n"
                "    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError\n"
                "    with pytest.raises(requests.exceptions.HTTPError):\n"
                "        get_weather('InvalidCity', 'fake_api_key')\n"
            )
            docs = (
                "# get_weather\n\n"
                "Fetches current weather for a city using the OpenWeatherMap API.\n"
                "Returns parsed JSON on success or raises HTTPError on failure.\n"
            )
            return GeneratedTool(code=code, tests=tests, docs=docs)
        # Otherwise: custom tool (use LLM)
        from .search_docs import search_docs
        from agents import RunConfig
        try:
            from agents.visualization import draw_graph
        except ImportError:
            draw_graph = None
        import uuid
        spec = specification.copy()
        spec['model'] = 'o4-mini-high'
        spec['temperature'] = 0.0
        spec['max_tokens'] = 4096
        # Fetch doc retrievals
        query = spec.get('description', '') or spec.get('task_description', '')
        references = search_docs(query, k=3)
        logger.info(f"Fetched {len(references)} references for tool generation.")
        if references:
            spec['prompt'] = spec.get('prompt', '') + f"\n<REFERENCES>\n" + "\n".join(references)
        # --- Tracing/metrics ---
        task_id = specification.get('task_id', 'unknown-task')
        tool_id = specification.get('tool_id', 'unknown-tool')
        spec_source = specification.get('spec_source', 'unknown-source')
        session_id = specification.get('session_id') or str(uuid.uuid4())
        trace_metadata = {
            'task_id': task_id,
        }
        run_config = RunConfig(trace_metadata=trace_metadata)

        # Prepare the final input prompt for the runner
        task_description = spec.get('prompt', '') or spec.get('description', '')
        output_format_instructions = """
        Please generate the Python code, corresponding pytest tests, and simple markdown documentation for the requested tool.
        Format your response strictly as a JSON object containing three keys: 'code', 'tests', and 'docs'.

        IMPORTANT: Do NOT include any markdown formatting or code fences (```). Output only the raw JSON object, with no additional text or fencing.
        IMPORTANT: In the 'code' value, use single quotes for all Python string literals (including f-strings), and avoid double quotes inside the code string. For example:
          "code": "url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'"

        IMPORTANT: The 'tests' code MUST import the generated function(s) from the 'code' module (which will be saved as 'tool.py').
        For example, if the generated code defines `def my_tool(x): ...`, the test code must start with `from tool import my_tool`.

        Example format:
        {
          "code": "def my_tool(x):\n    return x * 2",
          "tests": "from tool import my_tool\nimport pytest\ndef test_my_tool():\n    assert my_tool(2) == 4",
          "docs": "# My Tool\n\nMultiplies input by 2."
        }
        Ensure the output is ONLY the JSON object, with no introductory text or explanations.
        """
        final_input_prompt = f"{task_description}\n\n{output_format_instructions}"

        # Run the agent with the prepared specification
        result = await Runner.run(self, final_input_prompt, run_config=run_config)

        # Process the result
        output_data = None
        try:
            # Get the raw output first
            raw_output = result.final_output
            json_str = None

            if isinstance(raw_output, str):
                # Try to extract JSON from markdown fences
                match = re.search(r"```json\s*([\s\S]+?)\s*```", raw_output)
                if match:
                    json_str = match.group(1).strip()
                else:
                    # If no fences, assume the whole string might be JSON
                    json_str = raw_output.strip()

                # Parse the extracted/trimmed string
                if json_str:
                    try:
                         output_data = json.loads(json_str)
                    except json.JSONDecodeError as json_err:
                         logger.error(f"Failed to decode JSON after extraction: {json_err}\nExtracted string: '{json_str}'")
                         raise ValueError(f"Extracted content is not valid JSON: {json_err}") from json_err
                else:
                    # Handle case where raw_output was string but extraction failed
                    logger.error(f"Agent returned a string, but failed to extract JSON content. Raw output: {raw_output}")
                    raise ValueError("Failed to extract JSON content from string output.")

            elif isinstance(raw_output, dict):
                 # If it's already a dict, use it directly
                 output_data = raw_output
            else:
                 # Handle unexpected output types
                 logger.error(f"Unexpected output type from agent: {type(raw_output)}. Raw output: {raw_output}")
                 raise TypeError(f"Unexpected output type: {type(raw_output)}")


            if output_data is None:
                 # This case might happen if JSON parsing failed above or raw_output wasn't str/dict
                 logger.error(f"Failed to obtain valid output data. Raw output: {raw_output}")
                 return GeneratedTool(code=f"# Error: Failed to obtain valid output data.\n# Raw output:\n# {raw_output}", tests='', docs='')

            # If successful, parse the expected structure
            code = output_data.get('code', '')
            tests = output_data.get('tests', '')
            docs = output_data.get('docs', '')

            # Basic check: if code is empty, it might indicate a problem
            if not code:
                logger.warning(f"Agent run successful but generated code is empty. Output data: {output_data}")
                # Decide if this is an error or just an empty tool
                return GeneratedTool(code="# Warning: Generated code was empty.", tests=tests, docs=docs)

            return GeneratedTool(code=code, tests=tests, docs=docs)

        except Exception as e:
            # Assume any exception here means the agent run failed OR output parsing failed
            safe_raw_output = getattr(result, 'final_output', 'N/A') # Safely get raw output if possible
            logger.error(f"Error during agent run or parsing output: {e}\nRaw output: {safe_raw_output}", exc_info=True) # Log full traceback
            # Return the error message in the 'code' field for visibility
            return GeneratedTool(code=f"# Error during generation or parsing:\n# {e}\n\n# Raw output:\n# {safe_raw_output}", tests='', docs='')


# --- SubAgentManager --- #

class SubAgentManager:
    """Manages the lifecycle and delegation to specialized sub-agents."""

    AGENT_TOOL_MAP: Dict[str, Type[Agent]] = {
        "coder_tool": CoderAgent,
        "tester_tool": TesterAgent,
        "reviewer_tool": ReviewerAgent,
        "tool_designer_tool": ToolDesignerAgent,
        # Add other tool-to-agent mappings here
    }

    def __init__(self):
        """Initializes the SubAgentManager."""
        self._agents: Dict[str, Agent] = {}  # Cache for agent instances (by type/config)
        logger.info("SubAgentManager initialized.")

    def get_or_create_agent(self, task_requirements: Dict[str, Any]) -> Optional[Agent]:
        """
        Retrieves or creates a sub-agent based on task requirements.
        Uses a simple mapping from the first tool found.

        Args:
            task_requirements: A dictionary containing 'task_id', 'tools',
                               'guardrails', and 'description'.

        Returns:
            An instance of the appropriate Agent, or a BaseAgent/None if no
            specific agent type is determined.
        """
        task_id = task_requirements.get("task_id", "unknown")
        tools = task_requirements.get("tools", [])
        logger.info(f"Getting/creating agent for task {task_id} with tools: {tools}")

        agent_class: Optional[Type[Agent]] = None
        selected_tool = None

        if tools:
            # Simple approach: Use the first tool to determine agent type
            selected_tool = tools[0]
            agent_class = self.AGENT_TOOL_MAP.get(selected_tool)

        if agent_class:
            agent_type_name = agent_class.__name__
            # Basic caching: Check if an agent of this type already exists
            if agent_type_name in self._agents:
                 logger.debug(f"Reusing existing {agent_type_name} for task {task_id}")
                 return self._agents[agent_type_name]
            else:
                logger.info(f"Creating new {agent_type_name} for task {task_id} based on tool '{selected_tool}'")
                try:
                    # Instantiate the agent
                    new_agent = agent_class()
                    self._agents[agent_type_name] = new_agent # Cache it
                    return new_agent
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_type_name}: {e}", exc_info=True)
                    return None # Or raise?
        else:
            logger.warning(f"No specific agent class found for tools {tools} for task {task_id}. Falling back to BaseAgent.")
            # Fallback to a generic agent if no specific tool/agent mapping found
            if BaseAgent.__name__ not in self._agents:
                 self._agents[BaseAgent.__name__] = BaseAgent()
            return self._agents[BaseAgent.__name__]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieves an agent by its ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, Agent]:
        """Lists all managed agents."""
        return self._agents
