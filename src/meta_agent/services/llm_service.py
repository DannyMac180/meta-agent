"""
LLM Service for Code Generation.

This module provides the LLMService class which handles communication with
Large Language Model (LLM) APIs for code generation.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv
import aiohttp
import backoff

load_dotenv()

class LLMService:
    """
    Handles communication with LLM APIs for code generation.
    
    This class is responsible for making API calls to LLM providers,
    handling errors and retries, and extracting code from responses.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "o4-mini", 
                 max_retries: int = 3, timeout: int = 30,
                 api_base: Optional[str] = None):
        """
        Initialize the LLMService.
        
        Args:
            api_key: API key for the LLM provider. If None, attempts to load from OPENAI_API_KEY env var.
            model: Model to use for code generation
            max_retries: Maximum number of retries for failed API calls
            timeout: Timeout in seconds for API calls
            api_base: Base URL for the API (defaults to OpenAI's responses API)
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key not provided and not found in environment variables (OPENAI_API_KEY).")
            
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.api_base = api_base or "https://api.openai.com/v1/responses"
        self.logger = logging.getLogger(__name__)
        
    async def generate_code(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Generate code using the LLM API.
        
        This method sends a prompt to the LLM API and returns the generated code.
        It includes retry logic with exponential backoff for handling API errors.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Additional context for the LLM
            
        Returns:
            str: The generated code
            
        Raises:
            Exception: If code generation fails after all retries
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Calling LLM API (attempt {attempt + 1}/{self.max_retries})")
                response = await self._call_llm_api(prompt, context)
                code = self._extract_code_from_response(response)
                if code:
                    self.logger.info("Successfully generated code")
                    return code
                else:
                    self.logger.warning("Failed to extract code from response")
                    if attempt == self.max_retries - 1:
                        raise ValueError("Failed to extract code from LLM response")
            except Exception as e:
                self.logger.error(f"Error during LLM API call: {str(e)}", exc_info=True)
                if attempt == self.max_retries - 1:
                    raise e
                
                # Exponential backoff
                backoff_time = 2 ** attempt
                self.logger.info(f"Retrying in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to generate code after all retries")
    
    @backoff.on_exception(backoff.expo, 
                         (aiohttp.ClientError, asyncio.TimeoutError),
                         max_tries=3)
    async def _call_llm_api(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the LLM API with the given prompt and context.
        
        This method constructs the API request, sends it to the LLM provider,
        and returns the response.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Additional context for the LLM
            
        Returns:
            Dict[str, Any]: The API response
            
        Raises:
            aiohttp.ClientError: If the API call fails
            asyncio.TimeoutError: If the API call times out
            ValueError: If the API response is invalid
        """
        # Prepare the messages for the API
        messages = [
            {"role": "system", "content": "You are an expert Python developer tasked with implementing tools based on specifications."}
        ]
        
        # Add context as a system message if provided
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system", 
                "content": f"Here is additional context for the implementation:\n{context_str}"
            })
        
        # Add the main prompt as a user message
        messages.append({"role": "user", "content": prompt})
        
        # Prepare the API request payload
        payload = {
            "model": self.model,
            "input": messages,
            "max_output_tokens": 2000,  # Adjust based on expected code length
        }
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Make the API call
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"API error: {response.status} - {error_text}")
                    raise ValueError(f"API returned error: {response.status} - {error_text}")
                
                result = await response.json()
                return result
    
    def _extract_code_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract code from the LLM response.
        
        This method parses the LLM response to extract the generated code,
        handling different response formats and code block markers.
        
        Args:
            response: The API response from the LLM
            
        Returns:
            str: The extracted code, or an empty string if extraction fails
        """
        content_str = "" 
        try:
            if isinstance(response.get("output"), list):
                for item in response["output"]:
                    if isinstance(item, dict):
                        content = None
                        if isinstance(item.get("content"), list) and item["content"]:
                            first = item["content"][0]
                            if isinstance(first, dict) and isinstance(first.get("text"), str):
                                content = first["text"]
                        elif isinstance(item.get("text"), str):
                            content = item["text"]
                        if content:
                            content_str = content
                            break

            if not content_str:
                self.logger.error(
                    "Failed to extract content string from 'responses' endpoint. Expected 'output' list with a 'message' type item containing 'output_text'."
                )
                self.logger.debug(f"Full response for debugging: {json.dumps(response, indent=2)}")
                return ""

        except (KeyError, IndexError, TypeError) as e:
            self.logger.error(f"Error accessing content from 'responses' API structure: {e}")
            self.logger.debug(f"Full response for debugging: {json.dumps(response, indent=2)}")
            return ""
        
        try:
            # Try to extract code blocks with Python markers
            python_blocks = re.findall(r"```python\n(.*?)```", content_str, re.DOTALL)
            if python_blocks:
                return python_blocks[0].strip()
            
            # Try to extract any code blocks
            code_blocks = re.findall(r"```(.*?)```", content_str, re.DOTALL)
            if code_blocks:
                return code_blocks[0].strip()
            
            # If no code blocks found, try to extract based on common patterns
            lines = content_str.split("\n")
            code_lines = []
            in_code = False
            
            for line in lines:
                # Skip markdown headers and explanations
                if line.startswith("#") or ":" in line[:20]:
                    continue
                
                # Skip empty lines at the beginning
                if not in_code and not line.strip():
                    continue
                
                # Once we start collecting code, we're in code mode
                in_code = True
                code_lines.append(line)
            
            if code_lines:
                return "\n".join(code_lines).strip()
            
            # If all else fails, return the entire content
            self.logger.warning("Could not extract specific code blocks, returning full content")
            return content_str.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting code from response: {str(e)}", exc_info=True)
            return ""
