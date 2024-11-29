import asyncio
import ast
from typing import Tuple


class NotAllowedImportError(Exception):
    pass


async def write_to_file(filepath, file):
    with open(filepath, 'w') as f:
        code = file.read()
        f.write(code)
    return code

async def check_imports(code: str, allowed_imports: set):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name in allowed_imports:
                    raise NotAllowedImportError(f"Import '{alias.name}' is not allowed")
        if isinstance(node, ast.ImportFrom):
            if node.module not in allowed_imports:
                raise NotAllowedImportError(f"Import '{node.module}' is not allowed")
        

async def execute_code(file, args: Tuple, allowed_imports: set=None, timeout:int=5):
    """
    Args:
        file (UploadFile): the pure user uploaded file.
        allowed_imports (set): a set of allowed imports.
        **kwargs: keyword arguments to be passed to the solve function.

    Returns:
        dict: result of running code.

    Example:
        res = await execute_code(file, {'math', 'numpy'}, x=10, y=20)
    """
    if allowed_imports is None:
        allowed_imports = set()  # no imports allowed by default

    code = await write_to_file('uploaded_file.py', file)
    try:
        await check_imports(code, allowed_imports)
        import uploaded_file # type: ignore
        res = await asyncio.wait_for(uploaded_file.solve(*args), timeout=timeout)

    except AttributeError:
        return {
            "res": None,
            "error": "FunctionNotFoundError",
            "message": "Please wrap your solution in a function named 'solve'."
        }
    except NotAllowedImportError as e:
        return {
            "res": None,
            "error": "NotAllowedImportError",
            "message": str(e)
        }
    except asyncio.TimeoutError:
        return {
            "res": None,
            "error": "TimeoutError",
            "message": f"The code execution exceeded the time limit of {timeout} seconds."
        }
    except Exception as e:
        return {
            "res": None,
            "error": "ExecutionError",
            "message": f"An unexpected error occurred during code execution:\n{str(e)}"
        }

    return {"res": res, "error": None, "message": "Code executed successfully."}
