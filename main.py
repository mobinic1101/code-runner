from fastapi import FastAPI, File, UploadFile, Form
from typing import Annotated
from . import run_code, pydantic_models


app = FastAPI()


@app.post("/run-code")
async def run(python_file: Annotated[UploadFile, File], data: Annotated[pydantic_models.Data, Form]):
    pass
