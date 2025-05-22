
import importlib

def test_call():
    mod = importlib.import_module('tool')
    func = getattr(mod, 'add_numbers')
    func(a=1, b=1)
