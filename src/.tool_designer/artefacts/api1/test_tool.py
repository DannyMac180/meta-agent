from tool import get_weather
import pytest
import requests
from unittest.mock import patch

@patch('requests.get')
def test_get_weather_success(mock_get):
    mock_response = {
        'weather': [{'description': 'clear sky'}],
        'main': {'temp': 25.0}
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    result = get_weather('London', 'fake_api_key')
    assert result == mock_response

@patch('requests.get')
def test_get_weather_failure(mock_get):
    mock_get.return_value.status_code = 404
    # Configure the mock to raise HTTPError when raise_for_status is called
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
    with pytest.raises(requests.exceptions.HTTPError):
        get_weather('InvalidCity', 'fake_api_key')
