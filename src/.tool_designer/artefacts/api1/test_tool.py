
import importlib

def test_call():
    mod = importlib.import_module('tool')
    func = getattr(mod, 'get_weather')
    func(city='test', api_key='test')
