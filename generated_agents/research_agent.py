"""
Generated Agent - Created by Agent Generator

This agent was automatically generated based on the following specification:

    Create a web research agent that searches the web based on research questions and generates well-researched reports.
    
    Name: ResearchAgent
    
    Description: An advanced research agent that searches the web for information on complex topics, 
    analyzes multiple sources, and generates comprehensive, well-structured research reports with citations.
    
    Instructions: You are an expert research assistant specialized in web-based research. When given a research 
    question or topic, use your tools to search for relevant information across multiple sources. Analyze the 
    information for accuracy, relevance, and credibility. Synthesize findings into a comprehensive report that 
    includes:
    
    1. An executive summary of key findings
    2. A detailed analysis of the topic with supporting evidence
    3. Different perspectives or viewpoints when applicable
    4. Citations for all sources used
    5. Recommendations for further research if relevant
    
    Always prioritize high-quality, credible sources. When sources conflict, note the discrepancies and evaluate 
    the relative strength of each claim. Structure your reports in a logical, easy-to-follow format with clear 
    section headings. Use appropriate academic or professional language based on the research context.
    
    Tools needed:
    1. search_web: Searches the web for information
       - Parameters: 
           - query (string, required): The search query
           - num_results (integer, optional, default=8): Number of results to return
       - Returns: List of search results with titles, snippets, and URLs
    
    2. extract_content: Extracts the main content from a URL
       - Parameters: 
           - url (string, required): The URL to extract content from
       - Returns: The extracted text content
    
    3. analyze_source: Analyzes the credibility of a source
       - Parameters: 
           - url (string, required): The URL to analyze
           - content (string, required): The content to analyze
       - Returns: Credibility score and analysis
    
    4. summarize_content: Summarizes content from multiple sources
       - Parameters: 
           - texts (list of strings, required): List of texts to summarize
           - max_length (integer, optional, default=500): Maximum length of summary
       - Returns: Summarized text that synthesizes information from all sources
    
    Output type: A structured research report with sections for summary, analysis, findings, and references
    
    Guardrails:
    - Ensure all claims are supported by cited sources
    - Check for balanced representation of different viewpoints on controversial topics
    - Verify that sources are credible and relevant to the research question
    
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    function_tool,
    output_guardrail,
    GuardrailFunctionOutput
)

# Load environment variables from .env file
load_dotenv()

# Configure OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in the .env file or as an environment variable.")
    exit(1)


@function_tool
def search_web(query: str, num_results: int = 8) -> List[Dict[str, str]]:
    """
    Searches the web for information
    
    Args:
        query: The search query
        num_results: Number of results to return (default: 8)
        
    Returns:
        List of search results with titles, snippets, and URLs
    """
    import requests
    import json
    
    try:
        # This is a placeholder. In a real implementation, you would use a proper search API
        # such as Google Custom Search API, Bing Search API, or similar
        print(f"Searching the web for: {query}")
        
        # Simulated search results for demonstration
        results = [
            {
                "title": f"Result 1 for {query}",
                "snippet": f"This is a snippet of information about {query} from source 1.",
                "url": f"https://example.com/result1?q={query}"
            },
            {
                "title": f"Result 2 for {query}",
                "snippet": f"This is a snippet of information about {query} from source 2.",
                "url": f"https://example.com/result2?q={query}"
            }
        ]
        
        # In a production environment, replace with actual API call:
        # response = requests.get(
        #     "https://api.search.com/search",
        #     params={"q": query, "num": num_results},
        #     headers={"Authorization": f"Bearer {API_KEY}"}
        # )
        # results = response.json().get("results", [])
        
        return results[:num_results]
    except Exception as e:
        print(f"Error searching the web: {e}")
        return [{"title": "Error", "snippet": f"Failed to search: {str(e)}", "url": ""}]


@function_tool
def extract_content(url: str) -> str:
    """
    Extracts the main content from a URL
    
    Args:
        url: The URL to extract content from
        
    Returns:
        The extracted text content
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # This is a placeholder. In a real implementation, you would handle various edge cases
        print(f"Extracting content from: {url}")
        
        # Simulated content for demonstration
        if "example.com" in url:
            return f"This is the extracted content from {url}. It contains information relevant to the query."
        
        # In a production environment, use actual web scraping:
        # response = requests.get(url)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # 
        # # Remove script and style elements
        # for script in soup(["script", "style"]):
        #     script.extract()
        # 
        # # Get text
        # text = soup.get_text()
        # 
        # # Break into lines and remove leading and trailing space on each
        # lines = (line.strip() for line in text.splitlines())
        # # Break multi-headlines into a line each
        # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # # Drop blank lines
        # text = '\n'.join(chunk for chunk in chunks if chunk)
        # 
        # return text
        
        return "Simulated extracted content for demonstration purposes."
    except Exception as e:
        print(f"Error extracting content: {e}")
        return f"Failed to extract content from {url}: {str(e)}"


@function_tool
def analyze_source(url: str, content: str) -> Dict[str, Any]:
    """
    Analyzes the credibility of a source
    
    Args:
        url: The URL to analyze
        content: The content to analyze
        
    Returns:
        Credibility score and analysis
    """
    try:
        print(f"Analyzing source credibility: {url}")
        
        # This is a placeholder. In a real implementation, you would use more sophisticated
        # analysis techniques, possibly leveraging NLP or existing credibility databases
        
        # Simple domain-based credibility check
        credibility_score = 0.0
        analysis = ""
        
        # Educational or government sites generally have higher credibility
        if ".edu" in url:
            credibility_score = 0.9
            analysis = "Educational institution source, generally reliable."
        elif ".gov" in url:
            credibility_score = 0.9
            analysis = "Government source, generally reliable."
        elif ".org" in url:
            credibility_score = 0.7
            analysis = "Non-profit organization source, generally reliable but verify claims."
        elif "wikipedia" in url:
            credibility_score = 0.6
            analysis = "Wikipedia source, generally informative but should be verified with primary sources."
        elif "example.com" in url:
            credibility_score = 0.5
            analysis = "Example domain for demonstration purposes."
        else:
            credibility_score = 0.4
            analysis = "Unknown source credibility, exercise caution and verify information."
        
        # In a real implementation, you would analyze the content for:
        # - Presence of citations
        # - Writing style and tone
        # - Factual accuracy
        # - Bias indicators
        # - Publication date and recency
        
        return {
            "credibility_score": credibility_score,
            "analysis": analysis,
            "url": url
        }
    except Exception as e:
        print(f"Error analyzing source: {e}")
        return {
            "credibility_score": 0.0,
            "analysis": f"Failed to analyze source: {str(e)}",
            "url": url
        }


@function_tool
def summarize_content(texts: List[str], max_length: int = 500) -> str:
    """
    Summarizes content from multiple sources
    
    Args:
        texts: List of texts to summarize
        max_length: Maximum length of summary (default: 500)
        
    Returns:
        Summarized text that synthesizes information from all sources
    """
    try:
        print(f"Summarizing {len(texts)} text sources")
        
        # This is a placeholder. In a real implementation, you would use more sophisticated
        # summarization techniques, possibly leveraging NLP or LLM APIs
        
        # Simple concatenation and truncation for demonstration
        combined_text = " ".join(texts)
        
        if len(combined_text) <= max_length:
            return combined_text
        
        # Simple truncation (in a real implementation, use proper summarization)
        summary = combined_text[:max_length] + "..."
        
        # In a production environment, use a proper summarization technique:
        # from transformers import pipeline
        # summarizer = pipeline("summarization")
        # summary = summarizer(combined_text, max_length=max_length, min_length=min(100, max_length))
        # return summary[0]['summary_text']
        
        return summary
    except Exception as e:
        print(f"Error summarizing content: {e}")
        return f"Failed to summarize content: {str(e)}"


# Create the agent
researchagent = Agent(
    name="ResearchAgent",
    instructions="""
    You are an expert research assistant specialized in web-based research. When given a research 
    question or topic, use your tools to search for relevant information across multiple sources. Analyze the 
    information for accuracy, relevance, and credibility. Synthesize findings into a comprehensive report that 
    includes:
    
    1. An executive summary of key findings
    2. A detailed analysis of the topic with supporting evidence
    3. Different perspectives or viewpoints when applicable
    4. Citations for all sources used
    5. Recommendations for further research if relevant
    
    Always prioritize high-quality, credible sources. When sources conflict, note the discrepancies and evaluate 
    the relative strength of each claim. Structure your reports in a logical, easy-to-follow format with clear 
    section headings. Use appropriate academic or professional language based on the research context.
    
    Tools needed:
    1. search_web: Searches the web for information
       - Parameters: 
           - query (string, required): The search query
           - num_results (integer, optional, default=8): Number of results to return
       - Returns: List of search results with titles, snippets, and URLs
    
    2. extract_content: Extracts the main content from a URL
       - Parameters: 
           - url (string, required): The URL to extract content from
       - Returns: The extracted text content
    
    3. analyze_source: Analyzes the credibility of a source
       - Parameters: 
           - url (string, required): The URL to analyze
           - content (string, required): The content to analyze
       - Returns: Credibility score and analysis
    
    4. summarize_content: Summarizes content from multiple sources
       - Parameters: 
           - texts (list of strings, required): List of texts to summarize
           - max_length (integer, optional, default=500): Maximum length of summary
       - Returns: Summarized text that synthesizes information from all sources
    
    Output type: A structured research report with sections for summary, analysis, findings, and references
    
    Guardrails:
    - Ensure all claims are supported by cited sources
    - Check for balanced representation of different viewpoints on controversial topics
    - Verify that sources are credible and relevant to the research question
    
    """,
    tools=[search_web, extract_content, analyze_source, summarize_content],
)


async def main():
    """Run the ResearchAgent agent."""
    print("Welcome to the ResearchAgent!")
    print("Enter your query or 'exit' to quit.")
    
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        
        print("Processing your request...")
        result = await Runner.run(researchagent, input=user_input)
        
        print("\nResult:")
        print(result)
        print()

if __name__ == "__main__":
    asyncio.run(main())
