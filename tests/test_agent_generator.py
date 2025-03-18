"""
Test script for the Agent Generator

This script tests the Agent Generator with different agent specifications
to verify its functionality and refine the implementation.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from meta_agent.agent_generator import generate_agent

# Load environment variables from .env file
load_dotenv()

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in the .env file or as an environment variable:")
    print("export OPENAI_API_KEY='your-api-key'")
    print("Exiting tests.")
    sys.exit(1)

async def test_weather_agent():
    """Test generating a weather agent."""
    specification = """
    Create a weather agent that can provide weather information for cities.
    
    Name: WeatherAgent
    
    Description: An agent that provides current weather information for cities worldwide.
    
    Instructions: You are a helpful weather assistant. When users ask about the weather
    in a specific city, use the get_weather tool to fetch that information. If they ask
    for a forecast, use the get_forecast tool. Always provide temperatures in both
    Celsius and Fahrenheit. If a city cannot be found, politely inform the user.
    
    Tools needed:
    1. get_weather: Fetches current weather for a city
       - Parameters: city (string, required)
       - Returns: Weather data including temperature, conditions, humidity
    
    2. get_forecast: Fetches 5-day forecast for a city
       - Parameters: city (string, required), days (integer, optional, default=5)
       - Returns: Forecast data for each day
    
    Output type: A structured response with weather information
    
    Guardrails:
    - Validate that city names are non-empty strings
    - Ensure temperature values are reasonable (e.g., between -100°C and 100°C)
    """
    
    try:
        implementation = await generate_agent(specification)
        print("\nWeather Agent Test: SUCCESS")
        return True
    except Exception as e:
        print(f"\nWeather Agent Test: FAILED - {str(e)}")
        return False

async def test_research_agent():
    """Test generating a research agent."""
    specification = """
    Create a research agent that can search for information on topics.
    
    Name: ResearchAgent
    
    Description: An agent that can research topics and provide summaries of information.
    
    Instructions: You are a helpful research assistant. When users ask about a topic,
    use the search_web tool to find relevant information. Summarize the findings in a
    concise manner, providing citations for the sources used. If the topic is ambiguous,
    ask for clarification. Always prioritize reliable sources.
    
    Tools needed:
    1. search_web: Searches the web for information on a topic
       - Parameters: query (string, required), max_results (integer, optional, default=5)
       - Returns: List of search results with titles, snippets, and URLs
    
    2. fetch_content: Fetches the full content of a webpage
       - Parameters: url (string, required)
       - Returns: The text content of the webpage
    
    3. analyze_sentiment: Analyzes the sentiment of a text
       - Parameters: text (string, required)
       - Returns: Sentiment score (-1 to 1) and label (positive, negative, neutral)
    
    Output type: A structured research report
    
    Guardrails:
    - Validate that search queries are non-empty strings
    - Ensure URLs are properly formatted
    - Check that content is not offensive or inappropriate
    """
    
    try:
        implementation = await generate_agent(specification)
        print("\nResearch Agent Test: SUCCESS")
        return True
    except Exception as e:
        print(f"\nResearch Agent Test: FAILED - {str(e)}")
        return False

async def test_customer_service_agent():
    """Test generating a customer service agent."""
    specification = """
    Create a customer service agent that can handle common customer inquiries.
    
    Name: CustomerServiceAgent
    
    Description: An agent that handles customer service inquiries for an e-commerce store.
    
    Instructions: You are a helpful customer service representative for an online store.
    Help customers with order status inquiries, return requests, product information,
    and general questions. Use the appropriate tools to look up information and process
    requests. Be polite, professional, and empathetic in all interactions.
    
    Tools needed:
    1. check_order_status: Checks the status of an order
       - Parameters: order_id (string, required)
       - Returns: Order status information
    
    2. process_return: Initiates a return request
       - Parameters: order_id (string, required), reason (string, required)
       - Returns: Return confirmation and instructions
    
    3. get_product_info: Gets information about a product
       - Parameters: product_id (string, required)
       - Returns: Product details
    
    4. check_inventory: Checks if a product is in stock
       - Parameters: product_id (string, required), location (string, optional)
       - Returns: Inventory information
    
    Output type: A customer service response
    
    Guardrails:
    - Validate that order IDs and product IDs are in the correct format
    - Ensure responses are professional and empathetic
    - Check that return reasons are valid
    """
    
    try:
        implementation = await generate_agent(specification)
        print("\nCustomer Service Agent Test: SUCCESS")
        return True
    except Exception as e:
        print(f"\nCustomer Service Agent Test: FAILED - {str(e)}")
        return False

async def run_tests():
    """Run all tests and report results."""
    print("Running Agent Generator Tests...\n")
    
    results = []
    
    # Run tests
    results.append(await test_weather_agent())
    results.append(await test_research_agent())
    results.append(await test_customer_service_agent())
    
    # Report results
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"\nTest Results: {passed}/{total} passed, {failed}/{total} failed")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())
