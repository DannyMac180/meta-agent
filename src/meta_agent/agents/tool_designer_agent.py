import logging
from typing import Union, Dict, Any

from meta_agent.parsers.tool_spec_parser import ToolSpecificationParser
from meta_agent.generators.tool_code_generator import ToolCodeGenerator, CodeGenerationError

logger = logging.getLogger(__name__)

class ToolDesignerAgent:
    """Orchestrates the process of parsing a tool specification and generating code."""

    def __init__(self):
        """Initializes the Tool Designer Agent."""
        # Potential future setup, like loading configurations or models
        pass

    def design_tool(self, specification: Union[str, Dict[str, Any]]) -> str:
        """Parses the specification and generates the tool code.

        Args:
            specification: The tool specification (JSON/YAML string or dict).

        Returns:
            The generated Python code string for the tool.

        Raises:
            ValueError: If the specification is invalid.
            CodeGenerationError: If code generation fails.
        """
        logger.info("Starting tool design process...")

        # 1. Parse the specification
        parser = ToolSpecificationParser(specification)
        if not parser.parse():
            errors = parser.get_errors()
            logger.error(f"Specification parsing failed: {errors}")
            raise ValueError(f"Invalid tool specification: {'; '.join(errors)}")
        
        parsed_spec = parser.get_specification()
        if not parsed_spec:
             # This case should ideally not happen if parse() succeeded without errors
             logger.error("Specification parsed successfully but no spec object returned.")
             raise ValueError("Failed to retrieve parsed specification.")

        logger.info(f"Specification parsed successfully for tool: {parsed_spec.name}")

        # 2. Generate the code
        generator = ToolCodeGenerator(parsed_spec)
        try:
            generated_code = generator.generate()
            logger.info(f"Code generated successfully for tool: {parsed_spec.name}")
            return generated_code
        except CodeGenerationError as e:
            logger.error(f"Code generation failed for tool {parsed_spec.name}: {e}")
            raise # Re-raise the specific generation error
        except Exception as e:
            logger.exception(f"An unexpected error occurred during code generation for tool {parsed_spec.name}")
            # Wrap unexpected errors for consistency
            raise CodeGenerationError(f"Unexpected generation error: {e}")

# Example Usage (for interactive testing)
if __name__ == '__main__':
    # Example YAML spec (ensure valid paths if loading from file)
    example_yaml_spec = '''
    name: greet_user
    purpose: Greets the user by name.
    input_parameters:
      - name: user_name
        type: string
        description: The name of the user to greet.
        required: true
    output_format: string
    '''

    agent = ToolDesignerAgent()

    try:
        print("--- Designing Tool from YAML Spec ---")
        generated_code = agent.design_tool(example_yaml_spec)
        print("\n--- Generated Code --- \n")
        print(generated_code)
        print("\n--- End Generated Code ---")
    except (ValueError, CodeGenerationError) as e:
        print(f"\n--- Error Designing Tool --- \n{e}")

    # Example Invalid Spec
    invalid_spec = '{"name": "bad_tool"}' # Missing purpose, output_format
    try:
        print("\n--- Designing Tool from Invalid Spec ---")
        generated_code_invalid = agent.design_tool(invalid_spec)
        print("Generated code unexpectedly:", generated_code_invalid)
    except (ValueError, CodeGenerationError) as e:
        print(f"\n--- Error Designing Tool (Expected) --- \n{e}")
