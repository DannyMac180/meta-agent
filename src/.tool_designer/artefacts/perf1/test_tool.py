from tool import multiply
import pytest

def test_multiply_positive_numbers():
    assert multiply(3, 4) == 12

def test_multiply_negative_numbers():
    assert multiply(-2, -3) == 6

def test_multiply_positive_and_negative():
    assert multiply(-2, 3) == -6

def test_multiply_with_zero():
    assert multiply(5, 0) == 0
    assert multiply(0, 5) == 0

def test_multiply_large_numbers():
    assert multiply(100000, 100000) == 10000000000