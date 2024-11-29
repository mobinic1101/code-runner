from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form
import run_code

app = FastAPI()


@app.post("/run-code")
def run(python_file: Annotated[UploadFile, File]):
    pass