
import importlib

def test_call():
    mod = importlib.import_module('tool')
    func = getattr(mod, 'weather_fetcher')
    func(city='test', country_code='test')
