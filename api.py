from fastapi import FastAPI, HTTPException, Request
from fastapi.datastructures import UploadFile
import utils

app = FastAPI()

@app.post("/run-code")
async def run_code(request: Request):
    form = await request.form()
    python_file: UploadFile = form.get("python_file")
    if not python_file:
        raise HTTPException(status_code=400, detail="No file is uploaded.")
    utils.execute_code()
    
