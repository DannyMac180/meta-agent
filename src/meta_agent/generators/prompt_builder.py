"""
Prompt Builder for LLM-backed Code Generation.

This module provides the PromptBuilder class which creates effective prompts
for LLMs to generate tool implementation code based on specifications.
"""

import logging
from typing import Any, Dict, List


class PromptBuilder:
    """
    Creates effective prompts for LLMs based on tool specifications.
    
    This class is responsible for building prompts that will be sent to the LLM
    for generating tool implementation code. It supports different tool types
    with specialized prompt templates.
    """
    
    def __init__(self, prompt_templates: Dict[str, str]):
        """
        Initialize the PromptBuilder with prompt templates.
        
        Args:
            prompt_templates: Dictionary mapping tool types to prompt templates
        """
        self.prompt_templates = prompt_templates
        self.logger = logging.getLogger(__name__)
        
    def build_prompt(self, tool_specification: Any) -> str:
        """
        Build a prompt for the LLM based on the tool specification.
        
        This method determines the tool type, selects the appropriate template,
        and formats it with details from the tool specification.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            str: A formatted prompt for the LLM
        """
        tool_type = self._determine_tool_type(tool_specification)
        self.logger.debug(f"Determined tool type: {tool_type}")
        
        # Get the template for the tool type, or fall back to default
        template = self.prompt_templates.get(tool_type, self.prompt_templates.get("default"))
        if not template:
            self.logger.warning("No template found for tool type or default. Using basic template.")
            template = """
            Implement a Python tool with the following specifications:
            
            Tool Name: {name}
            Description: {description}
            
            Input Parameters:
            {input_params}
            
            Output Format:
            {output_format}
            
            Constraints:
            {constraints}
            """
        
        # Safely extract name and description
        name_attr = getattr(tool_specification, 'name', None)
        if not isinstance(name_attr, str) or not name_attr:
            name_attr = 'Unnamed Tool'
        description_attr = getattr(tool_specification, 'description', None)
        if not isinstance(description_attr, str) or not description_attr:
            description_attr = 'No description provided'
        formatted_prompt = template.format(
            name=name_attr,
            description=description_attr,
            input_params=self._format_input_params(getattr(tool_specification, 'input_params', [])),
            output_format=getattr(tool_specification, 'output_format', 'No output format specified'),
            constraints=self._format_constraints(getattr(tool_specification, 'constraints', []))
        )
        
        self.logger.debug("Prompt built successfully")
        return formatted_prompt
    
    def _determine_tool_type(self, tool_specification: Any) -> str:
        """
        Determine the type of tool based on the specification.
        
        This method analyzes the tool specification to determine its type,
        which is used to select the appropriate prompt template.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            str: The determined tool type
        """
        # Get the description and name for analysis
        description = getattr(tool_specification, 'description', '').lower()
        name = getattr(tool_specification, 'name', '').lower()
        
        # Check for API caller tools
        api_keywords = ['api', 'http', 'request', 'fetch', 'endpoint', 'rest']
        if any(keyword in description or keyword in name for keyword in api_keywords):
            return "api_caller"
        
        # Check for file manipulation tools first
        file_keywords = ['file', 'read', 'write', 'save', 'load', 'open', 'directory']
        if any(keyword in description or keyword in name for keyword in file_keywords):
            return "file_manipulator"
        # Check for data processing tools
        data_keywords = ['data', 'process', 'transform', 'convert', 'parse', 'format']
        if any(keyword in description or keyword in name for keyword in data_keywords):
            return "data_processor"
        
        # Default tool type
        return "default"
        
    def _format_input_params(self, input_params: List[Dict[str, Any]]) -> str:
        """
        Format input parameters for the prompt.
        
        This method formats the input parameters of the tool in a way that
        is clear and informative for the LLM.
        
        Args:
            input_params: List of input parameter dictionaries
            
        Returns:
            str: Formatted input parameters string
        """
        if not input_params:
            return "No input parameters"
        
        formatted_params = []
        for param in input_params:
            name = param.get('name', 'unnamed')
            param_type = param.get('type', 'any')
            description = param.get('description', 'No description')
            required = param.get('required', False)
            default = param.get('default', None)
            
            param_str = f"- {name} ({param_type}): {description}"
            if required:
                param_str += " [Required]"
            if default is not None:
                param_str += f" [Default: {default}]"
            
            formatted_params.append(param_str)
        
        return "\n".join(formatted_params)
        
    def _format_constraints(self, constraints: List[str]) -> str:
        """
        Format constraints for the prompt.
        
        This method formats the constraints of the tool in a way that
        is clear and informative for the LLM.
        
        Args:
            constraints: List of constraint strings
            
        Returns:
            str: Formatted constraints string
        """
        if not constraints:
            return "No specific constraints"
        
        return "\n".join(f"- {constraint}" for constraint in constraints)
