"""
String utilities for the meta-agent package.

This module provides functions for string manipulation.
"""

import re
from typing import List


def camel_to_snake(name: str) -> str:
    """
    Convert a camelCase or PascalCase string to snake_case.
    
    Args:
        name: String in camelCase or PascalCase
        
    Returns:
        String in snake_case
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert a snake_case string to camelCase.
    
    Args:
        name: String in snake_case
        
    Returns:
        String in camelCase
    """
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def snake_to_pascal(name: str) -> str:
    """
    Convert a snake_case string to PascalCase.
    
    Args:
        name: String in snake_case
        
    Returns:
        String in PascalCase
    """
    return ''.join(x.title() for x in name.split('_'))


def format_docstring(text: str, indent: int = 0) -> str:
    """
    Format a docstring with proper indentation.
    
    Args:
        text: Docstring text
        indent: Number of spaces to indent
        
    Returns:
        Formatted docstring
    """
    lines = text.strip().split('\n')
    indentation = ' ' * indent
    
    # Format the first line
    result = [f'{indentation}"""' + (lines[0] if lines else '')]
    
    # Add an empty line if there's more content
    if len(lines) > 1:
        if result[0][-1] != ' ':
            result[0] += ' '
        result.append('')
    
    # Add the rest of the lines
    for line in lines[1:]:
        result.append(f'{indentation}{line}')
    
    # Add the closing quotes
    result.append(f'{indentation}"""')
    
    return '\n'.join(result)
