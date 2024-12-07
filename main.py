from fastapi import FastAPI, File, UploadFile, Form, Response, status, BackgroundTasks
from typing import Annotated, List, Dict
import run_code, settings
from redis_operations import redis_operations


app = FastAPI()


@app.post("/run-code")
async def run(
    background_tasks: BackgroundTasks,
    python_file: Annotated[UploadFile, File],
    execution_id: Annotated[str, Form()],
    allowed_imports: Annotated[str, Form()],
    test_cases: Annotated[str, Form()],
):
    converted = run_code.convert_literal(test_cases)
    if not converted:
        return Response(
            f"invalid syntax in test_cases: {test_cases}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    allowed_imports = [item.strip() for item in allowed_imports.split(",")]
    test_cases = converted
    print(test_cases)

    res = await run_code.extract_function(python_file, allowed_imports)
    print(res)

    if res["error"]:
        print("ERROR OCCURRED DURING EXTRACTING FUNCTION")
        return res
    solve = res["func"]  # getting `solve` function
    background_tasks.add_task(
        run_code.run_tests, solve, test_cases, execution_id
    )

    return {"execution_id": execution_id}


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
