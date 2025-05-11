"""
Context Builder for LLM-backed Code Generation.

This module provides the ContextBuilder class which builds relevant context
for LLMs to generate high-quality tool implementation code.
"""

import logging
from typing import Any, Dict, List, Optional


class ContextBuilder:
    """
    Builds context for LLMs based on tool specifications.
    
    This class is responsible for creating rich context that helps the LLM
    generate better code, including information about the tool's purpose,
    input/output formats, similar examples, and best practices.
    """
    
    def __init__(self, examples_repository: Optional[Dict[str, Any]] = None):
        """
        Initialize the ContextBuilder with an examples repository.
        
        Args:
            examples_repository: Repository of example tools for reference
        """
        self.examples_repository = examples_repository or {}
        self.logger = logging.getLogger(__name__)
        
    def build_context(self, tool_specification: Any) -> Dict[str, Any]:
        """
        Build context for the LLM based on the tool specification.
        
        This method creates a comprehensive context object that includes
        various aspects of the tool specification to help the LLM generate
        better code.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            Dict[str, Any]: Context object for the LLM
        """
        self.logger.debug(f"Building context for tool: {getattr(tool_specification, 'name', 'unnamed')}")
        
        # Create the context dictionary
        context = {
            "tool_purpose": getattr(tool_specification, 'description', 'No description provided'),
            "input_output_formats": self._get_input_output_formats(tool_specification),
            "similar_examples": self._find_similar_examples(tool_specification),
            "best_practices": self._get_best_practices(tool_specification),
            "constraints": getattr(tool_specification, 'constraints', [])
        }
        
        self.logger.debug("Context built successfully")
        return context
    
    def _get_input_output_formats(self, tool_specification: Any) -> Dict[str, Any]:
        """
        Get input and output formats for the context.
        
        This method extracts and formats the input parameters and output format
        from the tool specification in a way that is helpful for the LLM.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            Dict[str, Any]: Dictionary containing input and output format information
        """
        input_params = getattr(tool_specification, 'input_params', [])
        output_format = getattr(tool_specification, 'output_format', None)
        
        # Format input parameters
        formatted_inputs = []
        for param in input_params:
            formatted_param = {
                "name": param.get('name', 'unnamed'),
                "type": param.get('type', 'any'),
                "description": param.get('description', 'No description'),
                "required": param.get('required', False),
                "default": param.get('default', None),
                "example_values": param.get('example_values', [])
            }
            formatted_inputs.append(formatted_param)
        
        # Format output
        formatted_output = {
            "description": output_format if isinstance(output_format, str) else "No output format specified",
            "type": "unknown"
        }
        
        # Try to determine output type if it's a dictionary
        if isinstance(output_format, dict):
            formatted_output = {
                "description": output_format.get('description', 'No output description'),
                "type": output_format.get('type', 'unknown'),
                "example": output_format.get('example', None)
            }
        
        return {
            "inputs": formatted_inputs,
            "output": formatted_output
        }
        
    def _find_similar_examples(self, tool_specification: Any) -> List[Dict[str, Any]]:
        """
        Find similar examples for the context.
        
        This method searches the examples repository for tools similar to the
        one being generated, based on keywords, functionality, or tool type.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            List[Dict[str, Any]]: List of similar example tools
        """
        if not self.examples_repository:
            self.logger.debug("No examples repository available")
            return []
        
        # Get tool name and description for matching
        tool_name = getattr(tool_specification, 'name', '').lower()
        tool_description = getattr(tool_specification, 'description', '').lower()
        
        # Extract keywords from the tool name and description
        keywords = set()
        for text in [tool_name, tool_description]:
            # Add individual words as keywords
            keywords.update(word.strip() for word in text.split() if len(word.strip()) > 3)
        
        # Find similar examples based on keyword matching
        similar_examples = []
        for example_name, example in self.examples_repository.items():
            # Skip if no example description
            example_description = example.get('description', '').lower()
            if not example_description:
                continue
            
            # Count matching keywords
            match_count = 0
            for keyword in keywords:
                if keyword in example_description or keyword in example_name.lower():
                    match_count += 1
            
            # If enough matches, add to similar examples
            if match_count >= 2:  # Threshold for similarity
                similar_examples.append({
                    "name": example_name,
                    "description": example.get('description', ''),
                    "implementation": example.get('implementation', ''),
                    "similarity_score": match_count
                })
        
        # Sort by similarity score (descending) and take top 3
        similar_examples.sort(key=lambda x: x['similarity_score'], reverse=True)
        top_examples = similar_examples[:3]
        
        self.logger.debug(f"Found {len(top_examples)} similar examples")
        return top_examples
        
    def _get_best_practices(self, tool_specification: Any) -> List[str]:
        """
        Get best practices for the context.
        
        This method provides a list of best practices for implementing the tool,
        based on the tool type, functionality, and general coding standards.
        
        Args:
            tool_specification: The specification for the tool
            
        Returns:
            List[str]: List of best practice recommendations
        """
        # Common best practices for all tools
        common_practices = [
            "Use descriptive variable names that reflect their purpose",
            "Include comprehensive error handling for all potential failure points",
            "Add type hints to improve code readability and enable static type checking",
            "Write clear docstrings explaining the purpose and usage of functions",
            "Follow PEP 8 style guidelines for Python code",
            "Validate input parameters before processing",
            "Use appropriate logging for errors and important events",
            "Return meaningful error messages when operations fail"
        ]
        
        # Get tool-specific best practices based on tool type
        tool_specific_practices = []
        
        # Determine tool type from name and description
        tool_name = getattr(tool_specification, 'name', '').lower()
        tool_description = getattr(tool_specification, 'description', '').lower()
        
        # Check for API caller tools
        api_keywords = ['api', 'http', 'request', 'fetch', 'endpoint', 'rest']
        if any(keyword in tool_description or keyword in tool_name for keyword in api_keywords):
            tool_specific_practices.extend([
                "Use the requests library for HTTP requests",
                "Implement proper error handling for API responses",
                "Add retry logic for transient failures",
                "Handle rate limiting with exponential backoff",
                "Set appropriate timeouts for API calls",
                "Validate and sanitize API responses before processing"
            ])
        
        # Check for data processing tools
        data_keywords = ['data', 'process', 'transform', 'convert', 'parse', 'format']
        if any(keyword in tool_description or keyword in tool_name for keyword in data_keywords):
            tool_specific_practices.extend([
                "Use appropriate data structures for efficient processing",
                "Consider memory usage for large datasets",
                "Implement validation for input data formats",
                "Provide clear error messages for malformed data",
                "Consider using generators for processing large datasets"
            ])
        
        # Check for file manipulation tools
        file_keywords = ['file', 'read', 'write', 'save', 'load', 'open', 'directory']
        if any(keyword in tool_description or keyword in tool_name for keyword in file_keywords):
            tool_specific_practices.extend([
                "Use context managers (with statements) for file operations",
                "Implement proper error handling for file operations",
                "Check file existence before operations",
                "Validate file paths for security concerns",
                "Handle file encoding correctly",
                "Consider using pathlib for path manipulations"
            ])
        
        # Combine common and tool-specific practices
        all_practices = common_practices + tool_specific_practices
        
        self.logger.debug(f"Compiled {len(all_practices)} best practices")
        return all_practices
