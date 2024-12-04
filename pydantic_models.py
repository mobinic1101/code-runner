from pydantic import BaseModel
from typing import Optional, List, Set, Tuple


class TestCase(BaseModel):
    id: int
    input: Tuple = (None)
    expected: Optional[List]


class Data(BaseModel):
    execution_id: str
    allowed_imports: Set[str]
    test_case: List[TestCase]
