import sys, types
try:
    import requests  # type: ignore
except ModuleNotFoundError:
    requests = types.ModuleType('requests')
    sys.modules['requests'] = requests

# always ensure 'get' exists so @patch('requests.get') works
if not hasattr(requests, 'get'):
    def _get(*_a, **_kw):
        raise RuntimeError('Network disabled in sandbox')
    requests.get = _get  # type: ignore[attr-defined]
def get_weather(city: str, api_key: str) -> dict:
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()
