from pydantic import BaseModel
from typing import List, Any

class TestCase(BaseModel):
    id: int
    input: Any
    expected: Any

class Data(BaseModel):
    execution_id: str
    allowed_imports: List[str]
    test_cases: List[TestCase]
