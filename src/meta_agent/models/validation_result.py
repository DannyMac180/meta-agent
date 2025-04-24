from pydantic import BaseModel
from typing import List

class ValidationResult(BaseModel):
    success: bool
    errors: List[str]
    coverage: float  # Line coverage as a float between 0 and 1
