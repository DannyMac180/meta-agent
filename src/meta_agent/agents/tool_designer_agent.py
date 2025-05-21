import logging
import os
from typing import Union, Dict, Any, Optional, List
from dataclasses import dataclass

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
    from agents import Agent
except ImportError:
    logging.warning("Failed to import 'Agent' from agents library. Using placeholder.")

    class Agent:
        def __init__(self, name=None, *args, **kwargs):
            pass

        async def run(self, *args, **kwargs):
            return {"error": "Base Agent class not available"}


from meta_agent.parsers.tool_spec_parser import ToolSpecificationParser
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
from meta_agent.research_manager import ToolResearchManager

logger = logging.getLogger(__name__)


@dataclass
class DesignRecord:
    """Track a tool design session."""

    spec: Any
    plan: Dict[str, Any]
    status: str = "created"


class ToolDesignerAgent(Agent):  # Inherit from Agent
    """Orchestrates the process of parsing a tool specification and generating code."""

    def __init__(
        self,
        model_name: str = "o4-mini-high",
        template_dir: Optional[str] = None,
        template_name: str = "tool_template.py.j2",
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4",
        examples_repository: Optional[Dict[str, Any]] = None,
        research_manager: Optional[ToolResearchManager] = None,
        enable_research: bool = False,
    ):
        """Initializes the Tool Designer Agent.

        Args:
            model_name (str): The name of the language model to use (if needed, e.g., for future LLM generation).
            template_dir (Optional[str]): Path to the directory containing Jinja2 templates.
                                         Defaults to '../templates' relative to this file.
            template_name (str): The name of the Jinja2 template file to use.
                                Defaults to 'tool_template.py.j2'.
            llm_api_key (Optional[str]): API key for the LLM service. If None, LLMService will try to load from env.
            llm_model (str): The model to use for LLM-backed generation.
            examples_repository (Optional[Dict[str, Any]]): Repository of example tools for reference.
        """
        super().__init__(
            name="ToolDesignerAgent", tools=[]
        )  # Initialize base Agent with name
        self.model_name = model_name
        self.template_name = template_name
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.examples_repository = examples_repository or {}
        self.research_manager = None
        if enable_research:
            self.research_manager = research_manager or ToolResearchManager()

        # Configuration placeholders (unused currently)
        # These attributes were previously used to control output style.
        # They are kept for potential future extension but default to None.
        self.code_style = None
        self.doc_style = None
        self.language = None
        self.test_style = None

        # Basic state tracking for executed designs
        self.design_history: List[DesignRecord] = []

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
        # _initialize_llm_components will handle cases where API key isn't available.
        self._initialize_llm_components(self.llm_api_key, self.llm_model)

    def _create_design_plan(self, spec: Any) -> Dict[str, Any]:
        """Create a simple design plan structure for the given spec."""
        return {
            "tool_name": getattr(spec, "name", "unknown"),
            "steps": [
                "parse_specification",
                "generate_code",
                "return_tool",
            ],
        }

    def get_design_history(self) -> List[DesignRecord]:
        """Return the history of design plans executed by this agent."""
        return self.design_history

    def _initialize_llm_components(self, api_key: Optional[str], model: str):
        """Initialize the LLM-backed code generation components."""
        try:
            # LLMService will use api_key if provided, otherwise try os.getenv("OPENAI_API_KEY")
            # It will raise ValueError if no key is found.
            self.llm_service = LLMService(api_key=api_key, model=model)

            # Initialize other components that depend on llm_service
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
            # This typically means LLMService couldn't find an API key.
            self.llm_service = None
            self.llm_code_generator = None
            logger.warning(
                f"Failed to initialize LLM components: {e}. LLM-backed generation will be disabled."
            )
        except Exception as e:
            # Catch any other unexpected errors during initialization
            self.llm_service = None
            self.llm_code_generator = None
            logger.error(
                f"Unexpected error initializing LLM components: {e}", exc_info=True
            )
            logger.warning(
                "LLM-backed generation will be disabled due to an unexpected error."
            )

    def design_tool(self, specification: Union[str, Dict[str, Any]]) -> str:
        """Parses the specification and generates tool code using a Jinja2 template."""
        try:
            # 1. Parse the specification
            parser = ToolSpecificationParser(specification)
            if not parser.parse():
                error_msgs = parser.get_errors()
                error_str = "; ".join(error_msgs)
                # Don't wrap this in a try-except - let it propagate directly
                raise ValueError(f"Invalid tool specification: {error_str}")

            parsed_spec = parser.get_specification()
            if parsed_spec is None:
                raise ValueError("Failed to parse tool specification")

            logger.info(
                f"Successfully parsed tool specification for: {parsed_spec.name}"
            )

            # 1.a. Create a simple design plan and record state
            plan = self._create_design_plan(parsed_spec)
            self.design_history.append(
                DesignRecord(spec=parsed_spec, plan=plan, status="parsed")
            )

            # 1.1. Map types to Python equivalents
            for param in parsed_spec.input_parameters:
                lower = param.type_.lower()
                param.type_ = TYPE_MAP.get(lower, param.type_)
            # Map output_format
            out_lower = parsed_spec.output_format.lower()
            parsed_spec.output_format = TYPE_MAP.get(
                out_lower, parsed_spec.output_format
            )

            # 2. Load the configured template
            try:
                template = self.jinja_env.get_template(self.template_name)
                logger.debug(f"Loaded template: {self.template_name}")
            except jinja2.TemplateNotFound:
                raise CodeGenerationError(
                    f"Tool template '{self.template_name}' not found"
                )
            except Exception as e:
                raise CodeGenerationError(f"Failed to load template: {e}")

            # 3. Render the template with the specification data
            try:
                generated_code = template.render(spec=parsed_spec)
                logger.info(
                    f"Successfully rendered template for tool: {parsed_spec.name}"
                )
                if self.design_history:
                    self.design_history[-1].status = "generated"
                return generated_code
            except Exception as e:
                raise CodeGenerationError(f"Failed to render template: {e}")

        except ValueError:
            # Let ValueError propagate through directly
            raise
        except CodeGenerationError:
            # Let CodeGenerationError propagate through directly
            raise
        except Exception as e:
            # Only wrap other exceptions
            logger.exception(f"Unexpected error in design_tool: {e}")
            raise CodeGenerationError(f"Unexpected error in design_tool: {e}")

    async def design_tool_with_llm(
        self, specification: Union[str, Dict[str, Any]]
    ) -> str:
        """
        Parses the specification and generates tool code using LLM-backed code generation.

        Args:
            specification: The tool specification, either as a string or dictionary

        Returns:
            str: The generated tool code

        Raises:
            ValueError: If the specification is invalid
            CodeGenerationError: If code generation fails
            RuntimeError: If LLM-backed generation is not available
        """
        if not self.llm_code_generator:
            raise RuntimeError(
                "LLM-backed code generation is not available. Please provide an API key."
            )

        try:
            # 1. Parse the specification
            parser = ToolSpecificationParser(specification)
            if not parser.parse():
                error_msgs = parser.get_errors()
                error_str = "; ".join(error_msgs)
                raise ValueError(f"Invalid tool specification: {error_str}")

            parsed_spec = parser.get_specification()
            if parsed_spec is None:
                raise ValueError("Failed to parse tool specification")

            logger.info(
                f"Successfully parsed tool specification for LLM generation: {parsed_spec.name}"
            )

            plan = self._create_design_plan(parsed_spec)
            self.design_history.append(
                DesignRecord(spec=parsed_spec, plan=plan, status="parsed")
            )

            # 2. Generate code using LLM
            try:
                logger.info("Generating code using LLM...")
                generated_code = await self.llm_code_generator.generate_code(
                    parsed_spec
                )
                logger.info(
                    f"Successfully generated code with LLM for tool: {parsed_spec.name}"
                )
                if self.design_history:
                    self.design_history[-1].status = "generated"
                return generated_code
            except Exception as e:
                logger.error(f"LLM code generation failed: {str(e)}", exc_info=True)
                raise CodeGenerationError(f"LLM code generation failed: {str(e)}")

        except ValueError:
            # Let ValueError propagate through directly
            raise
        except CodeGenerationError:
            # Let CodeGenerationError propagate through directly
            raise
        except Exception as e:
            # Only wrap other exceptions
            logger.exception(f"Unexpected error in design_tool_with_llm: {e}")
            raise CodeGenerationError(f"Unexpected error in design_tool_with_llm: {e}")

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full tool design workflow: research, parse, generate.

        Args:
            specification: Dictionary containing the tool specification and options
                          If 'use_llm' is True in the specification, LLM-backed generation will be used

        Returns:
            Dict[str, Any]: Result dictionary with status and output
        """
        logger.info(
            f"ToolDesignerAgent received run request for: {specification.get('name', 'Unknown Tool')}"
        )

        # Extract the actual specification content
        spec_content = specification  # Assuming the dict *is* the spec for now

        # Check if we should use LLM-backed generation

        use_llm = specification.get("use_llm", False)

        if not spec_content:
            return {
                "status": "error",
                "error": "No specification provided to ToolDesignerAgent",
            }

        try:
            # Parse once to support research step
            parser = ToolSpecificationParser(spec_content)
            if not parser.parse():
                error_str = "; ".join(parser.get_errors())
                return {
                    "status": "error",
                    "error": f"Invalid tool specification: {error_str}",
                }

            parsed_spec = parser.get_specification()
            if parsed_spec and self.research_manager:
                snippets = self.research_manager.research(
                    parsed_spec.name, parsed_spec.purpose
                )
                logger.debug("Research snippets gathered: %s", snippets)

            # Generate Code
            if use_llm and self.llm_code_generator:
                logger.info("Using LLM-backed code generation")
                generated_code = await self.design_tool_with_llm(spec_content)
            else:
                if use_llm and not self.llm_code_generator:
                    logger.warning(
                        "LLM-backed generation requested but not available. Falling back to template-based generation."
                    )
                logger.info("Using template-based code generation")
                generated_code = self.design_tool(spec_content)

            logger.info("Code generation successful.")

            # Generate Tests and Docs (placeholders)
            tests = "# TODO: Generate tests"
            docs = """# TODO: Generate documentation"""
            logger.debug("Using placeholder tests and docs.")

            # Return structure expected by manager
            result_tool = GeneratedTool(code=generated_code, tests=tests, docs=docs)
            return {
                "status": "success",
                "output": result_tool.model_dump(),  # Serialize the GeneratedTool object
            }

        except (ValueError, CodeGenerationError) as e:
            logger.error(f"Tool design failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in ToolDesignerAgent run")
            return {"status": "error", "error": f"Unexpected error: {e}"}

    async def refine_design(self, spec: Dict[str, Any], feedback: str) -> GeneratedTool:
        """Simple placeholder refinement implementation.

        The real implementation would leverage the original spec and feedback to
        modify the tool.  For testing we just append the feedback to the output
        message."""
        try:
            base_code = self.design_tool(spec)
        except Exception:
            name = spec.get("name", "Tool")
            base_code = f"""
import logging
logger_tool = logging.getLogger(__name__)

class {name}Tool:
    def __init__(self, salutation: str = 'Hello'):
        self.salutation = salutation

    def run(self, name: str) -> str:
        return f'{{self.salutation}}, {{name}} from {name}Tool!'

def get_tool_instance():
    return {name}Tool()
"""
        refined_code = base_code.replace(
            f"from {spec.get('name')}Tool!",
            f"from refined {spec.get('name')}Tool!",
        )
        return GeneratedTool(
            name=spec.get("name"),
            description=spec.get("description", "") + " (refined)",
            specification=spec.get("specification", {}),
            code=refined_code,
        )


# Example Usage (for interactive testing)
if __name__ == "__main__":
    import asyncio
    import os

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
        # Get API key from environment variable (LLMService will also do this if not passed)
        # api_key = os.environ.get("OPENAI_API_KEY")

        # Create agent. LLMService will try to get API_KEY from env if not provided.
        agent_template = ToolDesignerAgent()  # For template-based
        agent_llm = (
            ToolDesignerAgent()
        )  # For LLM-based (will use env key or passed key)
        # To test with an explicit key (e.g. if .env is not set or to override):
        # agent_llm_explicit_key = ToolDesignerAgent(llm_api_key="your_explicit_key_here")

        # Test template-based generation
        try:
            print("--- Designing Tool from YAML Spec (Template-based) ---")
            generated_code = agent_template.design_tool(example_yaml_spec)
            print("\n--- Generated Code --- \n")
            print(generated_code)
            print("\n--- End Generated Code ---")
        except (ValueError, CodeGenerationError) as e:
            print(f"\n--- Error Designing Tool --- \n{e}")

        # Test LLM-based generation if available
        if (
            agent_llm.llm_code_generator
        ):  # Check if LLM components were successfully initialized
            try:
                print("\n--- Designing Tool from YAML Spec (LLM-based) ---")
                generated_code_llm = await agent_llm.design_tool_with_llm(
                    example_yaml_spec
                )
                print("\n--- Generated Code (LLM) --- \n")
                print(generated_code_llm)
                print("\n--- End Generated Code (LLM) ---")
            except (ValueError, CodeGenerationError, RuntimeError) as e:
                print(f"\n--- Error Designing Tool with LLM --- \n{e}")
        else:
            print(
                "\n--- LLM-based generation not available (no API key found or error during init) ---"
            )

        # Example Invalid Spec
        invalid_spec = '{"name": "bad_tool"}'  # Missing purpose, output_format
        try:
            print("\n--- Designing Tool from Invalid Spec ---")
            generated_code_invalid = agent_template.design_tool(invalid_spec)
            print("Generated code unexpectedly:", generated_code_invalid)
        except (ValueError, CodeGenerationError) as e:
            print(f"\n--- Error Designing Tool (Expected) --- \n{e}")

    # Run the async test
    if __name__ == "__main__":
        asyncio.run(test_agent())
