"""
Decorators for the meta-agent package.

DEPRECATED: Use function_tool from the 'agents' package instead.
"""
import warnings
warnings.warn("meta_agent.decorators is deprecated. Use 'from agents import function_tool'.", DeprecationWarning, stacklevel=2)

def function_tool(*, name=None, description=None):
    """
    Decorator to mark a function as a tool.
    
    Args:
        name: Optional name for the tool. Defaults to the function name.
        description: Optional description for the tool. Defaults to the function docstring.
    """
    def decorator(func):
        func._function_tool = True
        func._name = name or func.__name__
        func._description = description or func.__doc__
        return func
    return decorator 