from tool import confusing_annotated_function
import pytest

def test_confusing_annotated_function():
    assert confusing_annotated_function([1, 2, 'a', 3]) == [1, 2, 3]
    assert confusing_annotated_function(['b', 'c', 4, 5]) == [4, 5]
    assert confusing_annotated_function([]) == []