from pydantic import BaseModel

class GeneratedTool(BaseModel):
    code: str  # Python source
    tests: str  # pytest source
    docs: str   # markdown docs
