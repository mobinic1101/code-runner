from pydantic import BaseModel
from typing import List, Tuple, Any, Union

class TestCase(BaseModel):
    id: int
    input: Union[Tuple, Any]
    expected: Any


class Data(BaseModel):
    execution_id: str
    allowed_imports: List[str]
    test_cases: List[TestCase]
