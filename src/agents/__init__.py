from __future__ import annotations


class Agent:
    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        tools: list | None = None,
    ) -> None:
        self.name = name or ""
        self.instructions = instructions or ""
        self.tools = tools or []

    async def run(self, *_args, **_kwargs):
        return {"status": "success"}


class Runner:
    async def run(self, agent: Agent, *args, **kwargs):
        return await agent.run(*args, **kwargs)


class Tool:
    pass


__all__ = ["Agent", "Runner", "Tool"]
