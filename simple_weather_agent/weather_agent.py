import asyncio
import json
import requests
from typing import Optional
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(location: str, units: Optional[str] = "metric") -> str:
    """
    Get current weather information for a location.
    
    Args:
        location: The city and state/country (e.g. "San Francisco, CA")
        units: Units of measurement, either "metric" or "imperial"
        
    Returns:
        JSON string containing weather information
    """
    # This is a mock implementation - in a real agent you would use a weather API
    weather_data = {
        "location": location,
        "temperature": 22 if units == "metric" else 72,
        "condition": "Sunny",
        "humidity": 45,
        "wind_speed": 10 if units == "metric" else 6.2
    }
    return json.dumps(weather_data)

# Create the weather agent
weather_agent = Agent(
    name="WeatherAgent",
    instructions="""
    You are a helpful weather assistant. You can provide current weather information, 
    forecasts, and weather-related advice.

    Your tasks include:
    1. Fetching weather data for a given location
    2. Providing weather forecasts
    3. Giving recommendations based on weather conditions

    When the user asks about the weather in a location, use the get_weather tool to 
    fetch the data.

    Be friendly, concise, and informative in your responses.
    """,
    tools=[get_weather]
)

# Create a runner for the agent
runner = Runner()

async def main():
    """Run the WeatherAgent."""
    print("Welcome to the WeatherAgent!")
    print("Enter your query or 'exit' to quit.")
    
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        
        print("Processing your request...")
        result = await runner.run(weather_agent, user_input)
        
        print("\nResult:")
        print(result)
        print()

if __name__ == "__main__":
    asyncio.run(main())
