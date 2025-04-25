from tool import multiply
import pytest
def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(-1, 5) == -5
    assert multiply(0, 10) == 0
    assert multiply(7, 0) == 0
    assert multiply(-3, -3) == 9
    assert multiply(2, -4) == -8