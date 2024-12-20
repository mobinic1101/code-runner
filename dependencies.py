from fastapi import Form, HTTPException
from typing import List, Dict
import run_code.utils

allowed_imports_description = "Comma separated list of allowed imports"
test_cases_description = "example: '[{'input': [1, 2, 3], 'output': 6}, {'input': [1, 2, 3], 'output': 6}]'"

def get_allowed_imports(allowed_imports: str=Form(..., description=allowed_imports_description)):
    """extract a list of allowed imports from a string

    Args:
        allowed_imports (str).

    Returns:
        List[str]
    """    
    return [item.strip() for item in allowed_imports.split(",")]

def get_test_cases(test_cases: str=Form(..., description=test_cases_description)) -> List[Dict]:
    result = run_code.utils.convert_literal(test_cases)
    if not result:
        raise HTTPException(status_code=422, detail="Invalid test cases")
    return result