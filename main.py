from typing import Annotated, List, Optional, Tuple, Set
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
import run_code


class TestCase(BaseModel):
    id: int
    input: Tuple = (None)
    expected: Optional[List]


class Data(BaseModel):
    allowed_imports: Set[str]
    test_case: List[TestCase]


app = FastAPI()


@app.post("/run-code")
async def run(python_file: Annotated[UploadFile, File], data: Annotated[Data, Form]):
    for test_case in data.test_case:
        res = await run_code.execute_code(python_file, test_case.input, data.allowed_imports)
        res["id"] = test_case.id
    return res
