"""
LLM-backed Code Generator for Tool Implementation.

This module provides the LLMCodeGenerator class which orchestrates the process
of generating tool implementation code using Large Language Models (LLMs).
"""

import logging
from typing import Any



class LLMCodeGenerator:
    """
    Orchestrates the code generation process using LLMs.
    
    This class coordinates the various components involved in generating
    tool implementation code using LLMs, including prompt building,
    context creation, LLM API calls, code validation, and fallback strategies.
    """
    
    def __init__(self, llm_service, prompt_builder, context_builder, 
                 code_validator, implementation_injector, fallback_manager):
        """
        Initialize the LLMCodeGenerator with its component services.
        
        Args:
            llm_service: Service for making LLM API calls
            prompt_builder: Builder for creating LLM prompts
            context_builder: Builder for creating context for the LLM
            code_validator: Validator for generated code
            implementation_injector: Injector for adding code to templates
            fallback_manager: Manager for handling generation failures
        """
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder
        self.context_builder = context_builder
        self.code_validator = code_validator
        self.implementation_injector = implementation_injector
        self.fallback_manager = fallback_manager
        self.logger = logging.getLogger(__name__)
        
    async def generate_code(self, tool_specification: Any) -> str:
        """
        Generate implementation code for a tool based on its specification.
        
        This method orchestrates the entire code generation process:
        1. Building a prompt based on the tool specification
        2. Creating context for the LLM
        3. Calling the LLM API to generate code
        4. Validating the generated code
        5. Implementing fallback strategies if validation fails
        6. Injecting the generated code into a tool template
        
        Args:
            tool_specification: The specification for the tool to be generated
            
        Returns:
            str: The complete tool code with the generated implementation
            
        Raises:
            Exception: If code generation fails and fallback strategies also fail
        """
        self.logger.info(f"Generating code for tool: {getattr(tool_specification, 'name', 'unnamed')}")
        
        # Build prompt and context
        prompt = self.prompt_builder.build_prompt(tool_specification)
        context = self.context_builder.build_context(tool_specification)
        
        try:
            # Generate code using LLM
            self.logger.debug("Calling LLM API to generate code")
            generated_code = await self.llm_service.generate_code(prompt, context)
            
            # Validate the generated code
            self.logger.debug("Validating generated code")
            validation_result = self.code_validator.validate(
                generated_code, tool_specification
            )
            
            # Handle validation failures
            if not validation_result.is_valid:
                self.logger.warning(
                    f"Code validation failed: {validation_result.get_all_issues()}"
                )
                # Use fallback output directly, skip template injection
                return await self.fallback_manager.handle_failure(
                    validation_result, tool_specification, prompt, context
                )
            
            # Inject the generated code into the tool template
            self.logger.debug("Injecting generated code into template")
            complete_tool_code = self.implementation_injector.inject(
                generated_code, tool_specification
            )
            self.logger.info("Code generation completed successfully")
            return complete_tool_code
            
        except Exception as e:
            self.logger.error(f"Error during code generation: {str(e)}", exc_info=True)
            return await self.fallback_manager.handle_exception(
                e, tool_specification, prompt, context
            )
