from fastapi import Form, File, HTTPException, UploadFile, Depends
from typing import List, Dict
import run_code.utils


allowed_imports_description = "Comma separated list of allowed imports example: 'math, os'"
test_cases_description = \
    "example: '[{'id': 1, 'input': [1, 2], 'output': 3}, {'id': 2, 'input': [1, 4], 'output': 5}]'"
function_not_found_description = """
Function 'solve' not found. please wrap your solution in a function called 'solve'.
"""


def get_allowed_imports(allowed_imports: str=Form(..., description=allowed_imports_description)):
    """extract a list of allowed imports from a string

    Args:
        allowed_imports (str).

    Returns:
        List[str]
    """    
    return [item.strip() for item in allowed_imports.split(",")]


def get_function(python_file: UploadFile=File(...), allowed_imports: List=Depends(get_allowed_imports)):
    python_file_ = run_code.utils.PythonFile(python_file, allowed_imports)
    is_valid, error_msg = python_file_.validate()
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)
    func = python_file_.extract_function("solve")
    if not func:
        raise HTTPException(status_code=422, detail=function_not_found_description)
    return func


def get_test_cases(test_cases: str=Form(..., description=test_cases_description)) -> List[Dict]:
    print(test_cases, f" before {type(test_cases)}")
    try:

        result = run_code.utils.convert_literal(test_cases)[0]
    except (SyntaxError, Exception) as e:
        raise HTTPException(status_code=422, detail="INVALID TEST CASE FORMAT: " + str(e))
    print(result, f" after {type(result)}")
    return result