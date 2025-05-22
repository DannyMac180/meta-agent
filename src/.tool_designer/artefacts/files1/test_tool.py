
import importlib

def test_call():
    mod = importlib.import_module('tool')
    func = getattr(mod, 'file_search')
    func(term='test', path='test')
