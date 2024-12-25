from fastapi import (
    FastAPI,
    Form,
    status,
    BackgroundTasks,
    Depends,
    HTTPException,
)
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict
from types import FunctionType
import json

import run_code.utils
import run_code.run_tests
from run_code.redis_operations import redis_operations
import settings
from dependencies import get_test_cases, get_function


app = FastAPI()


@app.post("/run-code")
def run(
    background_tasks: BackgroundTasks,
    function: Annotated[FunctionType, Depends(get_function)],
    execution_id: Annotated[str, Form()],
    test_cases: List[Dict] = Depends(get_test_cases),
):
    # run tests
    background_tasks.add_task(
        run_code.run_tests.run_tests,
        function=function,
        test_cases=test_cases,
        execution_id=execution_id,
    )

    return JSONResponse(
        content={"message": "Code execution started.", "execution_id": execution_id},
        status_code=status.HTTP_200_OK,
    )


@app.get("/get-result/{execution_id}")
def get_result(execution_id: str):
    result = redis_operations.get_value(execution_id)
    
    if not result:
        return HTTPException(status_code=404, detail="Execution not found.")

    json_result = json.loads(result)
    redis_operations.delete_key(execution_id)  # one-time use values
    return json_result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
