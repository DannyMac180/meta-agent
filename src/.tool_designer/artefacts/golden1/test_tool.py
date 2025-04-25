from tool import add
import pytest
def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
    assert add(-5, -7) == -12
    assert add(100, 200) == 300