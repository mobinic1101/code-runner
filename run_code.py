import ast
import json
import os
from typing import Tuple, List
from concurrent.futures import ThreadPoolExecutor
from .pydantic_models import TestCase
from . import redis_operations


FILE_PATH = "./uploaded_files/uploaded_file.py"


class NotAllowedImportError(Exception):
    pass


def write_to_file(filepath, file):
    with open(filepath, "w") as f:
        code = file.read()
        f.write(code)
    return code


def check_imports(code: str, allowed_imports: set):
    """validate the imports of the file

    Args:
        code (str): the content returned by file.read()
        allowed_imports (set): a set of allowed imports

    Raises:
        NotAllowedImportError: if an invalid import was found.
    """

    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name in allowed_imports:
                    raise NotAllowedImportError(f"Import '{alias.name}' is not allowed")
        if isinstance(node, ast.ImportFrom):
            if node.module not in allowed_imports:
                raise NotAllowedImportError(f"Import '{node.module}' is not allowed")


# async def execute_code(file, args: Tuple, allowed_imports: set=None, timeout:int=5):
#     """
#     Args:
#         file (UploadFile): the pure user uploaded file.
#         allowed_imports (set): a set of allowed imports.
#         **kwargs: keyword arguments to be passed to the solve function.

#     Returns:
#         dict: result of running code.

#     Example:
#         res = await execute_code(file, {'math', 'numpy'}, x=10, y=20)
#     """
#     if allowed_imports is None:
#         allowed_imports = set()  # no imports allowed by default

#     code = write_to_file('uploaded_file.py', file)
#     try:
#         check_imports(code, allowed_imports)
#         import uploaded_file # type: ignore
#         res = await asyncio.wait_for(uploaded_file.solve(*args), timeout=timeout)

#     except AttributeError:
#         return {
#             "res": None,
#             "error": "FunctionNotFoundError",
#             "message": "Please wrap your solution in a function named 'solve'."
#         }
#     except NotAllowedImportError as e:
#         return {
#             "res": None,
#             "error": "NotAllowedImportError",
#             "message": str(e)
#         }
#     except asyncio.TimeoutError:
#         return {
#             "res": None,
#             "error": "TimeoutError",
#             "message": f"The code execution exceeded the time limit of {timeout} seconds."
#         }
#     except Exception as e:
#         return {
#             "res": None,
#             "error": "ExecutionError",
#             "message": f"An unexpected error occurred during code execution:\n{str(e)}"
#         }

#     return {"res": res, "error": None, "message": "Code executed successfully."}


def extract_function(python_file, allowed_imports: set = None):
    """validate imports of the file and extract the solve function.

    Args:
        python_file (UploadFile): the user uploaded file.
        allowed_imports (set, optional): Defaults to None.

    Returns:
        dictionary: {"func": function, "error": str, "error_message": str}
    """

    result = {"func": None, "error": None, "error_message": None}

    if not allowed_imports:
        allowed_imports = set()

    # writing the file to storage getting it ready to get imported
    code = write_to_file(FILE_PATH, python_file)

    try:
        check_imports(code, allowed_imports)
        import uploaded_file  # type: ignore

        result["func"] = uploaded_file.solve
    except NotAllowedImportError as e:
        result["error"] = "NotAllowedImportError"
        result["error_message"] = str(e)
    except AttributeError:
        result["error"] = "FunctionNotFoundError"
        result["error_message"] = (
            "Please wrap your solution in a function named 'solve'."
        )
    os.remove(FILE_PATH) # cleanup!
    return result


def execute_function(func, args: Tuple, test_case_id: int):
    """
    Args:
        func (_type_): the `solve` function.
        test_case_id (int)

    Returns:
        dict: {"id": test_case id(int), "output": str|None, "error": str|None, "error_message": str|None}
    """
    result = {"id": test_case_id, "output": None, "error": None, "error_message": None}
    try:
        output = func(*args)
        result["output"] = output
    except Exception as e:
        result["error"] = "ExecutionError"
        result["error_message"] = str(e)
    return result


def run_tests(func, test_cases: List[TestCase], execution_id: str):
    result = {"execution_id": execution_id, "test_result": None, "error": None}
    with ThreadPoolExecutor() as executor:
        futures = []
        for test_case in test_cases:
            future = executor.submit(
                execute_function,
                **{"func": func, "args": test_case.input, "test_case_id": test_case.id},
            )
            futures.append(future)

        try:
            future = executor.submit(
                lambda futures: [future.result() for future in futures], futures
            )
            result["test_result"] = future.result(timeout=5)
        except TimeoutError as e:
            result["error"] = (
                f"TimeoutError: The execution of test cases exceeded the allowed time limit of 5 seconds\
                      Please check if the function is taking too long to execute or\
                          if there are any infinite loops in the test cases."
            )
    
        

# we are gonna use redis to store the result of test cases in a hash with `execution_id` as key of it.
    
