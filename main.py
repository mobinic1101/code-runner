from fastapi import FastAPI, File, UploadFile, Form, status, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict
import run_code.utils
import run_code.run_tests
from run_code.redis_operations import redis_operations
import settings
from dependencies import get_allowed_imports, get_test_cases


app = FastAPI()


@app.post("/run-code")
def run(
    background_tasks: BackgroundTasks,
    python_file: Annotated[UploadFile, File],
    execution_id: Annotated[str, Form()],
    allowed_imports: List[str] = Depends(get_allowed_imports),
    test_cases: List[Dict] = Depends(get_test_cases),
):
    source_code = python_file.file.read().decode("utf-8")
    print(source_code)

    # validate file
    run_code.utils.validate_file(source_code, allowed_imports)

    # extract the `solve()` function
    func = run_code.utils.extract_function(source_code, "solve")

    # run tests
    background_tasks.add_task(run_code.run_tests.run_tests, func, test_cases, execution_id)

    return JSONResponse(
        content={"message": "Code execution started.", "execution_id": execution_id},
        status_code=status.HTTP_200_OK,
    )


@app.get("/get-result/{execution_id}")
def get_result(execution_id: str):
    result = redis_operations.get_value(execution_id)
    if not result:
        return HTTPException(status_code=404, detail="Execution not found.")

    redis_operations.delete_key(execution_id)  # one-time use values
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
