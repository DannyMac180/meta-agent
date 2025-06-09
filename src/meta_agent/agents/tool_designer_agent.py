# ruff: noqa: E402,F401
import logging
import os
from typing import Union, Dict, Any, Optional, List

# --- Jinja2 Import ---
import jinja2

# Mapping from spec type strings to Python types
TYPE_MAP = {
    "integer": "int",
    "string": "str",
    "float": "float",
    "boolean": "bool",
    "any": "Any",
}

# --- Import base Agent, handling potential unavailability ---
try:
    from agents import Agent as _Agent
except ImportError:
    logging.warning("Failed to import 'Agent' from agents library. Using placeholder.")

    class _Agent:
        def __init__(self, name: str | None = None, *_: Any, **__: Any) -> None:
            self.name = name or "StubAgent"

        async def run(self, *_a: Any, **_kw: Any) -> Dict[str, Any]:
            return {"error": "Base Agent class not available"}


BaseAgent = _Agent


from meta_agent.parsers.tool_spec_parser import (
    ToolSpecificationParser,
    ToolSpecification,
)
from meta_agent.generators.tool_code_generator import CodeGenerationError
from meta_agent.models.generated_tool import GeneratedTool

# Import LLM-backed code generation components
from meta_agent.generators.llm_code_generator import LLMCodeGenerator
from meta_agent.generators.prompt_builder import PromptBuilder
from meta_agent.generators.context_builder import ContextBuilder
from meta_agent.generators.code_validator import CodeValidator
from meta_agent.generators.implementation_injector import ImplementationInjector
from meta_agent.generators.fallback_manager import FallbackManager
from meta_agent.generators.prompt_templates import PROMPT_TEMPLATES
from meta_agent.services.llm_service import LLMService

# Tests/doc generators kept from subtask 11.9
from meta_agent.generators.test_generator import generate_basic_tests

logger = logging.getLogger(__name__)


class ToolDesignerAgent(BaseAgent):
    """Orchestrates the process of parsing a tool specification and generating code."""

    def __init__(
        self,
        model_name: str = "o4-mini-high",
        template_dir: Optional[str] = None,
        template_name: str = "tool_template.py.j2",
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4",
        examples_repository: Optional[Dict[str, Any]] = None,
    ):
        """Initializes the Tool Designer Agent.

        Args:
            model_name (str): The name of the language model to use.
            template_dir (Optional[str]): Path to the directory containing Jinja2 templates.
            template_name (str): The name of the Jinja2 template file to use.
            llm_api_key (Optional[str]): API key for the LLM service. If None, LLMService will try to load from env.
            llm_model (str): The model to use for LLM-backed generation.
            examples_repository (Optional[Dict[str, Any]]): Repository of example tools for reference.
        """
        super().__init__(name="ToolDesignerAgent", tools=[])  # Initialize base Agent

        self.model_name = model_name
        self.template_name = template_name
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.examples_repository = examples_repository or {}

        # Configuration placeholders for future extension
        self.code_style = None
        self.doc_style = None
        self.language = None
        self.test_style = None

        # Determine template directory
        if template_dir is None:
            self.template_dir = os.path.join(
                os.path.dirname(__file__), "..", "templates"
            )
        else:
            self.template_dir = template_dir

        # --- Jinja2 Environment Setup ---
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        self.jinja_env.globals["map_type"] = lambda t: TYPE_MAP.get(t.lower(), t)
        logger.info(f"Jinja environment loaded from: {self.template_dir}")

        # Always attempt to initialize LLM components.
        self._initialize_llm_components(self.llm_api_key, self.llm_model)

    # --------------------------------------------------------------------- #
    # --------------------------  Helper Methods  ------------------------- #
    # --------------------------------------------------------------------- #

    def _generate_basic_docs(self, spec: ToolSpecification) -> str:
        """Return minimal documentation for a generated tool."""
        lines: List[str] = [
            f"# {spec.name}",
            "",
            spec.purpose,
            "",
            "## Inputs",
        ]
        for p in spec.input_parameters:
            req = "(Required)" if p.required else "(Optional)"
            lines.append(f"- {p.name}: {p.description or 'No description'} {req}")
        lines.append("")
        lines.append("## Output")
        lines.append(str(spec.output_format))
        return "\n".join(lines)

    def _initialize_llm_components(self, api_key: Optional[str], model: str):
        """Initialize the LLM-backed code generation components."""
        try:
            self.llm_service = LLMService(api_key=api_key, model=model)

            self.prompt_builder = PromptBuilder(PROMPT_TEMPLATES)
            self.context_builder = ContextBuilder(self.examples_repository)
            self.code_validator = CodeValidator()
            self.implementation_injector = ImplementationInjector(self.jinja_env)
            self.fallback_manager = FallbackManager(
                self.llm_service, self.prompt_builder
            )

            self.llm_code_generator = LLMCodeGenerator(
                llm_service=self.llm_service,
                prompt_builder=self.prompt_builder,
                context_builder=self.context_builder,
                code_validator=self.code_validator,
                implementation_injector=self.implementation_injector,
                fallback_manager=self.fallback_manager,
            )
            logger.info(
                "LLM-backed code generation components initialized successfully."
            )

        except ValueError as e:
            self.llm_service = None
            self.llm_code_generator = None
            logger.warning(
                f"Failed to initialize LLM components: {e}. LLM-backed generation disabled."
            )
        except Exception:
            self.llm_service = None
            self.llm_code_generator = None
            logger.error("Unexpected error initializing LLM components", exc_info=True)
            logger.warning("LLM-backed generation disabled due to an unexpected error.")

    # --------------------------------------------------------------------- #
    # ----------------------  Template-Based Design  ---------------------- #
    # --------------------------------------------------------------------- #

    def design_tool(self, specification: Union[str, Dict[str, Any]]) -> str:
        """Parse the specification and generate tool code using a Jinja2 template."""
        try:
            parser = ToolSpecificationParser(specification)
            if not parser.parse():
                raise ValueError(
                    f"Invalid tool specification: {'; '.join(parser.get_errors())}"
                )

            parsed_spec = parser.get_specification()
            if parsed_spec is None:
                raise ValueError("Failed to parse tool specification")

            # Normalise types
            for param in parsed_spec.input_parameters:
                param.type_ = TYPE_MAP.get(param.type_.lower(), param.type_)
            parsed_spec.output_format = TYPE_MAP.get(
                parsed_spec.output_format.lower(), parsed_spec.output_format
            )

            # Render template
            try:
                template = self.jinja_env.get_template(self.template_name)
            except jinja2.TemplateNotFound:
                raise CodeGenerationError(
                    f"Tool template '{self.template_name}' not found"
                )

            return template.render(spec=parsed_spec)

        except (ValueError, CodeGenerationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in design_tool: {e}")
            # Chain the original exception to preserve context
            raise CodeGenerationError(f"Unexpected error in design_tool: {e}") from e

    # --------------------------------------------------------------------- #
    # ---------------------  LLM-Backed Code Generation  ------------------- #
    # --------------------------------------------------------------------- #

    async def design_tool_with_llm(
        self, specification: Union[str, Dict[str, Any]]
    ) -> str:
        """Generate tool code using the LLM pipeline."""
        if not self.llm_code_generator:
            raise RuntimeError(
                "LLM-backed generation not available (provide an API key)."
            )

        try:
            parser = ToolSpecificationParser(specification)
            if not parser.parse():
                raise ValueError(
                    f"Invalid tool specification: {'; '.join(parser.get_errors())}"
                )

            parsed_spec = parser.get_specification()
            if parsed_spec is None:
                raise ValueError("Failed to parse tool specification")

            return await self.llm_code_generator.generate_code(parsed_spec)

        except (ValueError, CodeGenerationError):
            raise
        except Exception as e:
            logger.exception("Unexpected error in design_tool_with_llm")
            raise CodeGenerationError(f"Unexpected error in design_tool_with_llm: {e}")

    # --------------------------------------------------------------------- #
    # ----------------------------  Agent Run  ---------------------------- #
    # --------------------------------------------------------------------- #

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full tool-design workflow: parse spec → generate code (+ tests & docs).

        If ``use_llm`` is True in the specification, the LLM pipeline is used.
        """
        logger.info(
            f"ToolDesignerAgent received request for: {specification.get('name', 'Unknown')}"
        )

        if not specification:
            return {"status": "error", "error": "No specification provided"}

        use_llm = specification.get("use_llm", False)

        try:
            parser = ToolSpecificationParser(specification)
            if not parser.parse():
                return {
                    "status": "error",
                    "error": f"Invalid tool specification: {'; '.join(parser.get_errors())}",
                }

            parsed_spec = parser.get_specification()
            assert parsed_spec is not None  # For mypy / static checkers

            # Choose generation path
            if use_llm and self.llm_code_generator:
                generated_code = await self.design_tool_with_llm(specification)
            else:
                if use_llm and not self.llm_code_generator:
                    logger.warning(
                        "LLM generation requested but unavailable – falling back to template."
                    )
                generated_code = self.design_tool(specification)

            # Basic tests & docs (kept from subtask 11.9)
            tests = generate_basic_tests(parsed_spec)
            docs = self._generate_basic_docs(parsed_spec)

            result_tool = GeneratedTool(code=generated_code, tests=tests, docs=docs)
            output = (
                result_tool.model_dump()
                if hasattr(result_tool, "model_dump")
                else result_tool.dict()
            )
            return {"status": "success", "output": output}

        except (ValueError, CodeGenerationError) as e:
            logger.error("Tool design failed", exc_info=True)
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in ToolDesignerAgent run")
            return {"status": "error", "error": f"Unexpected error: {e}"}


# ------------------------------------------------------------------------- #
# ---------------------------  Example Usage  ----------------------------- #
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    import asyncio

    # Example YAML spec
    example_yaml_spec = """
    name: greet_user
    purpose: Greets the user by name.
    input_parameters:
      - name: user_name
        type: string
        description: The name of the user to greet.
        required: true
    output_format: string
    """

    async def test_agent():
        agent = ToolDesignerAgent()  # Template-based

        print("--- Designing Tool (template) ---")
        try:
            code = agent.design_tool(example_yaml_spec)
            print(code)
        except (ValueError, CodeGenerationError) as err:
            print("Error:", err)

        if agent.llm_code_generator:
            print("\n--- Designing Tool (LLM) ---")
            try:
                code_llm = await agent.design_tool_with_llm(example_yaml_spec)
                print(code_llm)
            except Exception as err:
                print("LLM Error:", err)
        else:
            print("\nLLM generation not available (no API key).")

    asyncio.run(test_agent())
