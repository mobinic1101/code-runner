import ast
from typing import List
from fastapi import HTTPException


def get_ast(source_code: str):
    """get the Abstract Syntax Tree of a file

    Args:
        file (file like object eg. open("file.py", "r")): UploadFile
    
    Returns:
        ast.AST: the AST of the file
    """
    tree = ast.parse(source=source_code)
    return tree


def validate_file(source_code: str, allowed_imports: List):
    """validate the imports of the file as well as any syntax errors

    Args:
        tree (ast.AST): the AST of the file
        allowed_imports (set): a set of allowed imports

    Raises:
        HTTPException: if there are any SyntaxErrors or if an invalid import was found
    """
    # check for any syntax errors
    try:
        tree = get_ast(source_code=source_code)
    except (SyntaxError, Exception) as e:
        raise HTTPException(status_code=422, detail=f"VALIDATION ERROR: {str(e)}")
    
    # check for any invalid imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name in allowed_imports:
                    raise HTTPException(422, f"VALIDATION ERROR: Import '{alias.name}' is not allowed")
        if isinstance(node, ast.ImportFrom):
            if node.module not in allowed_imports:
                raise HTTPException(422, f"VALIDATION ERROR: Import '{node.module}' is not allowed")

def _execute_python_code(source_code):
    """
    Executes Python code from a string.
    Returns a list:
    [error_message (if any), namespace with executed code (if successful)].
    """
    result = [None, None]
    try:        
        # Compile and execute the code
        compiled = compile(source_code, "<received_file>", "exec") 
        namespace = {}
        exec(compiled, namespace)
        result[1] = namespace  # Store the namespace if successful
    except (SyntaxError, Exception) as e:
        result[0] = str(e)  # Store the error message if an exception occurs
    
    return result


def extract_function(source_code: str, func_name: str):
    """extracts a function from a python source code

    Args:
        source_code (str): string representation of a python file
        func_name (str): function name to get extracted

    Raises:
        HTTPException: if the function is not found

    Returns:
        FunctionType
    """    

    error, namespace = _execute_python_code(source_code)
    if error or not namespace:
        raise HTTPException(status_code=422, detail=error)

    func = namespace.get(func_name)
    return func
    

def convert_literal(test_cases):
    """convert a string representation of List/Tuple into a list[objects].

    Args:
        test_cases: [str]: string representation of objects to get converted
    Returns:
        list: list of converted datatypes
        False: if any errors occurred during conversion
    """
    obj =  ast.literal_eval(test_cases)
    if not isinstance(obj, tuple):
        obj = [obj]
    return obj
