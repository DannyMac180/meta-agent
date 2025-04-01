# test_json_spec.py
import asyncio
import json
from meta_agent import generate_agent

async def main():
    # JSON specification
    specification = json.dumps({
        "name": "ResearchAgent",
        "description": "An agent that performs web research on topics",
        "instructions": "You are a research assistant that helps users find information on various topics. Use the search tool to find relevant information and summarize it concisely.",
        "tools": [
            {
                "name": "search_web",
                "description": "Searches the web for information",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "The search query",
                        "required": True
                    },
                    {
                        "name": "num_results",
                        "type": "integer",
                        "description": "Number of results to return",
                        "required": False
                    }
                ],
                "return_type": "string"
            }
        ],
        "output_type": "string",
        "guardrails": [
            {
                "description": "Ensure sources are cited properly",
                "implementation": "Check that responses include source citations"
            }
        ]
    })
    
    # Generate the agent
    implementation = await generate_agent(specification, output_dir="./generated_research_agent")
    
    # Print the implementation
    print("Agent implementation generated successfully!")
    print("\nMain file preview:")
    print(implementation.main_file[:500] + "..." if len(implementation.main_file) > 500 else implementation.main_file)

if __name__ == "__main__":
    asyncio.run(main())
