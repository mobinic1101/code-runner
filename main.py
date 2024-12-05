from fastapi import FastAPI, File, UploadFile, Form, Response, status, BackgroundTasks
from typing import Annotated
from . import run_code, pydantic_models
from .redis_operations import redis_operations


app = FastAPI()


@app.post("/run-code")
async def run(
    python_file: Annotated[UploadFile, File],
    data: Annotated[pydantic_models.Data, Form],
    background_tasks: BackgroundTasks
):
    res = run_code.extract_function(python_file, data.allowed_imports)

    if res["error"]:
        return Response(res, status.HTTP_422_UNPROCESSABLE_ENTITY)
        
    solve = res["func"]  # getting `solve` function
    background_tasks.add_task(run_code.run_tests, *(solve, data.test_cases, data.execution_id))

    return Response(content={"execution_id": data.execution_id}, status_code=status.HTTP_202_ACCEPTED)


@app.get("/get-result/{execution_id}")
async def get_result(execution_id: str):
    result = redis_operations.get_all_from_hash(execution_id)
    if not result:
        return Response(status=status.HTTP_404_NOT_FOUND)

    redis_operations.delete_key(execution_id) # one time use values
    return result
