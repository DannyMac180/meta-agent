from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any


class SpecSchema(BaseModel):
    """Defines the specification for the meta-agent."""

    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Brief description of the agent")
    goal: str = Field(..., description="Goal of the agent")
    io_contract: 'IOContract' = Field(..., description="Input/output contract for the agent")
    tools: List['Tool'] = Field(default_factory=list, description="List of tools available to the agent")
    guardrails: List['Guardrail'] = Field(default_factory=list, description="List of guardrails for agent behavior")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Constraints for agent operation")
    instructions: List[str] = Field(default_factory=list, description="Instructions for the agent to follow")

    @validator("name", "description", "goal")
    def not_empty(cls, v, field):
        if not v or not v.strip():
            raise ValueError(f"{field.name} must not be empty")
        return v

    @validator("tools", each_item=True)
    def validate_tool(cls, v):
        if not v.name.strip():
            raise ValueError("Tool name must not be empty")
        return v

    @classmethod
    def example(cls) -> "SpecSchema":
        """Returns an example SpecSchema instance."""
        return cls(
            name="ExampleAgent",
            description="An example agent specification",
            goal="An example goal",
            io_contract=IOContract(input="in", output="out"),
            tools=[Tool(name="Tool1", description="Example tool")],
            guardrails=[Guardrail(rule="Do not break rules")],
            constraints={"max_steps": 5},
            instructions=[
                "Do X",
                "Then do Y"
            ],
        )


class IOContract(BaseModel):
    input: str = Field(..., description="Input contract for the agent")
    output: str = Field(..., description="Output contract for the agent")


class Tool(BaseModel):
    name: str = Field(..., description="Name of the tool")
    description: Optional[str] = Field(None, description="Tool description")


class Guardrail(BaseModel):
    rule: str = Field(..., description="Guardrail rule for agent behavior")
