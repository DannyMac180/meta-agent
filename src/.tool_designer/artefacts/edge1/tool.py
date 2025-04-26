def confusing_annotated_function(lst: int) -> str:
    result = [x for x in lst if isinstance(x, int)]
    return result