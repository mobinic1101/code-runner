from fastapi import FastAPI, File, UploadFile, Form, status, BackgroundTasks, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict
from run_code.exceptions import NotAllowedImportError
import run_code.utils
import run_code.run_tests
from run_code import redis_operations
import settings
from dependencies import get_allowed_imports, get_test_cases


app = FastAPI()


def validate_imports(python_file, allowed_imports: List[str]):
    tree = run_code.utils.get_ast(python_file)
    try:
        run_code.utils.validate_imports(tree, allowed_imports)
    except NotAllowedImportError as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/run-code")
async def run(
    background_tasks: BackgroundTasks,
    python_file: Annotated[UploadFile, File],
    execution_id: Annotated[str, Form()],
    allowed_imports: List[str] = Depends(get_allowed_imports),
    test_cases: List[Dict] = Depends(get_test_cases),
):
    # validate imports
    validate_imports(python_file, allowed_imports)

    # extract the `solve()` function
    error, func = run_code.utils.extract_function(python_file, "solve")
    if error:
        print("ERROR OCCURRED DURING EXTRACTING FUNCTION")
        raise HTTPException(status_code=422, detail="Error occurred during extracting function")

    # run tests
    background_tasks.add_task(run_code.run_tests.run_tests, func, test_cases, execution_id)

    return JSONResponse(
        content={"message": "Code execution started.", "execution_id": execution_id},
        status_code=status.HTTP_200_OK,
    )


@app.get("/get-result/{execution_id}")
async def get_result(execution_id: str):
    result = redis_operations.get_all_from_hash(execution_id)
    if not result:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    redis_operations.delete_key(execution_id)  # one-time use values
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
