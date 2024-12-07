import ast
import json
import os
from typing import Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis_operations
import settings


FILE_PATH = "./uploaded_files/uploaded_file.py"
redis_client = redis_operations.RedisOperations()


class NotAllowedImportError(Exception):
    pass


async def write_to_file(filepath, file):
    with open(filepath, "w") as f:
        code =  await file.read()
        code = code.decode("utf-8")
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


def convert_literal(test_cases):
    """convert a string representation of various data types (like lists, 
    dictionaries, strings, or integers) back into their actual data types.

    Args:
        objects: List[str]: string representation of objects to get converted
    Returns:
        list: list of converted datatypes
    """
    try:
        obj =  ast.literal_eval(test_cases)
        if not isinstance(obj, tuple):
            obj = [obj]
        return obj
    except ValueError as e:
        print("ERROR WHILE CONVERTING LITERALS: ", e)
        return False


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


async def extract_function(python_file, allowed_imports: List = None):
    """validate imports of the file and extract the solve function.

    Args:
        python_file (UploadFile): the user uploaded file.
        allowed_imports (set, optional): Defaults to None.

    Returns:
        dictionary: {"func": function, "error": str, "error_message": str}
    """

    result = {"func": None, "error": None, "error_message": None}

    if not allowed_imports:
        allowed_imports = []

    # writing the file to storage getting it ready to get imported
    code = await write_to_file(FILE_PATH, python_file)
    print("incoming code:\n\t", code)
    print("file exists?: ", os.path.exists(FILE_PATH))

    try:
        check_imports(code, allowed_imports)
        from uploaded_files import uploaded_file  # type: ignore

        result["func"] = uploaded_file.solve
    except NotAllowedImportError as e:
        result["error"] = "NotAllowedImportError"
        result["error_message"] = str(e)
    except AttributeError:
        result["error"] = "FunctionNotFoundError"
        result["error_message"] = (
            "Please wrap your solution in a function named 'solve'."
        )
    except Exception as e:
        result["error"] = "Error"
        result["error_message"] = (
            str(e)
        )
    os.remove(FILE_PATH) # cleanup!
    return result


def _execute_function(func, args: Tuple):
    """
    Args:
        func (_type_): the `solve` function.
        test_case_id (int)

    Returns:
        dict: {"id": test_case id(int), "output": str|None, "error": str|None, "error_message": str|None}
    """
    result = {"output": None, "error": None, "error_message": None}
    try:
        output = func(*args)
        result["output"] = output
    except Exception as e:
        result["error"] = "ExecutionError"
        result["error_message"] = str(e)
    return result


def run_tests(func, test_cases: List[Dict], execution_id: str):
    """run test cases in a thread pool using `concurrent.futures.ThreadPoolExecutor`.
    if the `func` is a blocking function or it took more than {} seconds

    Args:
        func (_type_): _description_
        test_cases (List[TestCase]): _description_
        execution_id (str): _description_
    """
    final_result = {"execution_id": execution_id, "test_result": []}
    with ThreadPoolExecutor() as executor:
        for test_case in test_cases:
            test_result = {"id": None, "result": None, "error": None, "error_message": None}
            future = executor.submit(
                _execute_function,
                **{"func": func, "args": test_case.get("input")},
            )
            try:
                # future = executor.submit(
                #     lambda futures: [future.result() for future in futures], futures
                # )
                # result["test_result"] = future.result(timeout=settings.RUN_TESTS_TIMEOUT)
                # print("futures: " ,futures)
                test_result["id"] = test_case.get("id")
                solve_result = future.result(timeout=settings.RUN_TESTS_TIMEOUT)
                test_result["result"] = solve_result["output"]
                test_result["error"] = solve_result["error"]
                test_result["error_message"] = solve_result["error_message"]
            except TimeoutError as e:
                test_result["error"] = "TimeoutError"
                test_result["error_message"] = (
    f"""The execution of test case {test_case.get("id")} exceeded the allowed time limit of
        {settings.RUN_TESTS_TIMEOUT} seconds;
        Please check if the function is taking too long to execute or
        if there are any infinite loops in the test case."""
                )
            final_result["test_result"].append(test_result)
    redis_client.set_value(key=execution_id, value=json.dumps(final_result), ex=settings.REDIS_EXPIRE_SEC)

    
