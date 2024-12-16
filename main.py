from fastapi import FastAPI, File, UploadFile, Form, status, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict
import run_code
from run_code import redis_operations
import run_code.utils
import settings


app = FastAPI()


@app.post("/run-code")
async def run(
    background_tasks: BackgroundTasks,
    python_file: Annotated[UploadFile, File],
    execution_id: Annotated[str, Form()],
    allowed_imports: Annotated[
        str, Form(description="Comma separated list of allowed imports")
    ],
    test_cases: Annotated[
        str,
        Form(
            description="example: '[{'input': [1, 2, 3], 'output': 6}, {'input': [1, 2, 3], 'output': 6}]'"
        ),
    ],
):
    converted = run_code.utils.convert_literal(test_cases)
    if not converted:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "Invalid test cases"},
        )

    allowed_imports = [item.strip() for item in allowed_imports.split(",")]
    test_cases = converted
    print(test_cases)

    error, func = run_code.utils.extract_function(python_file, "solve")

    if error:
        print("ERROR OCCURRED DURING EXTRACTING FUNCTION")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": error},
        )

    background_tasks.add_task(run_code.run_tests, func, test_cases, execution_id)

    return JSONResponse(
        content={"message": "Code execution started.", "execution_id": execution_id},
        status_code=status.HTTP_200_OK,
    )


@app.get("/get-result/{execution_id}")
async def get_result(execution_id: str):
    result = redis_operations.get_all_from_hash(execution_id)
    if not result:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    redis_operations.delete_key(execution_id)  # one time use values
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT)
