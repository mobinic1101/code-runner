from fastapi import (
    FastAPI,
    Request,
    status,
    BackgroundTasks,
    Depends,
    HTTPException,
)
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict
from types import FunctionType
import json
import uuid

import run_code.utils
import run_code.run_tests
from run_code.redis_operations import redis_operations
import settings
from dependencies import get_test_cases, get_function
from decorators import prevent_overlapping_process


app = FastAPI()


@app.post("/run-code")
@prevent_overlapping_process
def run(
    request: Request,
    background_tasks: BackgroundTasks,
    function: Annotated[FunctionType, Depends(get_function)],
    test_cases: List[Dict] = Depends(get_test_cases),
):
    ip_addr = request.client.host
    execution_id = str(uuid.uuid4())
    
    # run tests
    background_tasks.add_task(
        run_code.run_tests.run_tests,
        function=function,
        test_cases=test_cases,
        execution_id=execution_id,
        userid=ip_addr
    )

    return JSONResponse(
        content={"message": "execution started.", "execution_id": execution_id},
        status_code=status.HTTP_200_OK,
    )


@app.get("/get-result/{execution_id}", description="retrieve the result of a user's execution")
def get_result(execution_id: str, request: Request):
    ip_addr = request.client.host
    result = redis_operations.get_value(execution_id)
    print(ip_addr, result)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Execution not found.")

    json_result = json.loads(result)

    # allow users to submit future processes
    redis_operations.delete_key(ip_addr)
    redis_operations.delete_key(execution_id)
    return json_result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
