"""
Implementation-related data models for the meta-agent package.

This module contains the AgentImplementation model that defines the complete
implementation of an agent with all files.
"""

from typing import Dict
from pydantic import BaseModel, Field


class AgentImplementation(BaseModel):
    """Complete agent implementation with all files."""
    main_file: str = Field(description="Content of the main Python file")
    additional_files: Dict[str, str] = Field(description="Additional files needed (filename: content)")
    installation_instructions: str = Field(description="Instructions for installing dependencies")
    usage_examples: str = Field(description="Examples of how to use the agent")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'additional_files' not in data:
            data['additional_files'] = {}
        super().__init__(**data)
