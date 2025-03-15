"""
Test script for the Agent Generator

This script tests the Agent Generator with different agent specifications
to verify its functionality and refine the implementation.
"""

import asyncio
import os
import sys
from agent_generator import generate_agent

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key using:")
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
    - Check if the weather data contains sensitive information
    """
    
    print("\n===== Testing Weather Agent Generation =====")
    try:
        implementation = await generate_agent(specification)
        print("Weather Agent generation successful!")
        
        # Save the implementation
        with open("weather_agent.py", "w") as f:
            f.write(implementation.main_file)
        print("Saved weather agent to weather_agent.py")
        
        # Save additional files
        for filename, content in implementation.additional_files.items():
            with open(filename, "w") as f:
                f.write(content)
            print(f"Saved additional file to {filename}")
            
        return True
    except Exception as e:
        print(f"Error generating Weather Agent: {e}")
        return False

async def test_research_agent():
    """Test generating a research agent."""
    specification = """
    Create a research agent that can search for information and summarize findings.
    
    Name: ResearchAgent
    
    Description: An agent that can search for information on various topics and provide
    summarized findings with citations.
    
    Instructions: You are a research assistant. When users ask for information on a topic,
    use the search_web tool to find relevant information. Summarize the findings in a
    concise manner, providing citations for the sources used. If the topic is ambiguous,
    ask for clarification. Always prioritize reliable sources.
    
    Tools needed:
    1. search_web: Searches the web for information
       - Parameters: query (string, required), num_results (integer, optional, default=5)
       - Returns: List of search results with titles, snippets, and URLs
    
    2. extract_content: Extracts the main content from a URL
       - Parameters: url (string, required)
       - Returns: The extracted text content
    
    3. summarize_text: Summarizes a long text
       - Parameters: text (string, required), max_length (integer, optional, default=200)
       - Returns: Summarized text
    
    Output type: A structured response with research findings and citations
    
    Guardrails:
    - Validate that search queries are appropriate
    - Ensure citations are included for all information
    - Check for balanced viewpoints on controversial topics
    """
    
    print("\n===== Testing Research Agent Generation =====")
    try:
        implementation = await generate_agent(specification)
        print("Research Agent generation successful!")
        
        # Save the implementation
        with open("research_agent.py", "w") as f:
            f.write(implementation.main_file)
        print("Saved research agent to research_agent.py")
        
        # Save additional files
        for filename, content in implementation.additional_files.items():
            with open(filename, "w") as f:
                f.write(content)
            print(f"Saved additional file to {filename}")
            
        return True
    except Exception as e:
        print(f"Error generating Research Agent: {e}")
        return False

async def test_customer_service_agent():
    """Test generating a customer service agent."""
    specification = """
    Create a customer service agent that can handle common customer inquiries.
    
    Name: CustomerServiceAgent
    
    Description: An agent that handles customer service inquiries, including order status,
    returns, and product information.
    
    Instructions: You are a customer service representative. Help customers with their
    inquiries about orders, returns, and products. Use the appropriate tools to fetch
    information and provide helpful responses. Be polite and professional at all times.
    If you cannot resolve an issue, offer to escalate it to a human representative.
    
    Tools needed:
    1. check_order_status: Checks the status of an order
       - Parameters: order_id (string, required)
       - Returns: Order status information
    
    2. process_return: Initiates a return process
       - Parameters: order_id (string, required), reason (string, required)
       - Returns: Return confirmation and instructions
    
    3. get_product_info: Gets information about a product
       - Parameters: product_id (string, required)
       - Returns: Product details
    
    Handoffs:
    - HumanAgent: For complex issues that require human intervention
    
    Guardrails:
    - Validate order IDs and product IDs
    - Ensure sensitive customer information is not exposed
    - Check for appropriate language and tone
    """
    
    print("\n===== Testing Customer Service Agent Generation =====")
    try:
        implementation = await generate_agent(specification)
        print("Customer Service Agent generation successful!")
        
        # Save the implementation
        with open("customer_service_agent.py", "w") as f:
            f.write(implementation.main_file)
        print("Saved customer service agent to customer_service_agent.py")
        
        # Save additional files
        for filename, content in implementation.additional_files.items():
            with open(filename, "w") as f:
                f.write(content)
            print(f"Saved additional file to {filename}")
            
        return True
    except Exception as e:
        print(f"Error generating Customer Service Agent: {e}")
        return False

async def run_tests():
    """Run all tests and report results."""
    print("Starting Agent Generator Tests")
    
    results = {
        "Weather Agent": await test_weather_agent(),
        "Research Agent": await test_research_agent(),
        "Customer Service Agent": await test_customer_service_agent()
    }
    
    print("\n===== Test Results =====")
    all_passed = True
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. See above for details.")

if __name__ == "__main__":
    asyncio.run(run_tests())
