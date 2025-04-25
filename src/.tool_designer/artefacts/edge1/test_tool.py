from tool import confusing_function
import pytest

def test_confusing_function():
    assert confusing_function(['1', '2', '3']) == [1, 2, 3]
    assert confusing_function(['10', '20']) == [10, 20]
    assert confusing_function([]) == []