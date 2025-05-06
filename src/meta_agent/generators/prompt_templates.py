"""
Prompt Templates for LLM-backed Code Generation.

This module provides prompt templates for different tool types to be used
by the PromptBuilder when creating prompts for LLM code generation.
"""

# Dictionary of prompt templates for different tool types
PROMPT_TEMPLATES = {
    "default": """
    You are an expert Python developer tasked with implementing a tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Be efficient and follow Python best practices
    2. Include proper error handling
    3. Be well-documented with docstrings
    4. Include type hints
    5. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "api_caller": """
    You are an expert Python developer tasked with implementing an API-calling tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Use the requests library for HTTP requests
    2. Include proper error handling for API errors
    3. Implement appropriate retry logic
    4. Handle rate limiting gracefully
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "data_processor": """
    You are an expert Python developer tasked with implementing a data processing tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Use efficient data structures and algorithms
    2. Handle different data formats appropriately
    3. Include proper error handling for malformed data
    4. Be memory-efficient for large datasets
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "file_manipulator": """
    You are an expert Python developer tasked with implementing a file manipulation tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Use context managers (with statements) for file operations
    2. Include proper error handling for file operations
    3. Validate file paths for security concerns
    4. Handle file encoding correctly
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "text_processor": """
    You are an expert Python developer tasked with implementing a text processing tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Handle text efficiently, considering encoding issues
    2. Use appropriate string manipulation techniques
    3. Consider performance for large text inputs
    4. Include proper error handling
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "database_tool": """
    You are an expert Python developer tasked with implementing a database interaction tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Use parameterized queries to prevent SQL injection
    2. Implement proper connection management
    3. Include error handling for database errors
    4. Use connection pooling if appropriate
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """,
    
    "calculation_tool": """
    You are an expert Python developer tasked with implementing a calculation or algorithm tool based on the following specification:
    
    Tool Name: {name}
    Description: {description}
    
    Input Parameters:
    {input_params}
    
    Output Format:
    {output_format}
    
    Constraints:
    {constraints}
    
    Please implement this tool in Python. Your implementation should:
    1. Use efficient algorithms and data structures
    2. Handle edge cases appropriately
    3. Include proper error handling for invalid inputs
    4. Consider numerical stability if applicable
    5. Be well-documented with docstrings
    6. Include type hints
    7. Only include the implementation code, not the class definition or imports
    
    Provide only the Python code without any additional explanation or markdown formatting.
    """
}
