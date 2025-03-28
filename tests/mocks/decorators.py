"""
Mock decorators for testing.
"""

def function_tool(*, name=None, description=None):
    """Mock function_tool decorator."""
    def decorator(func):
        func._function_tool = True
        func._name = name or func.__name__
        func._description = description or func.__doc__
        return func
    return decorator 