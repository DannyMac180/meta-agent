# WeatherAgent implementation
import os
import asyncio
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, output_guardrail, GuardrailFunctionOutput







agent = Agent(
    name="WeatherAgent",
    instructions="You are a helpful weather assistant."
)

async def run_agent(input_text):
    runner = Runner()
    result = await Runner.run(agent, input_text)
    return result