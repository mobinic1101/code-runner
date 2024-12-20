import ast
from typing import List
from .exceptions import NotAllowedImportError


def get_ast(file):
    """get the Abstract Syntax Tree of a file

    Args:
        file (file like object eg. open("file.py", "r")): UploadFile
    
    Returns:
        ast.AST: the AST of the file
    """
    return ast.parse(file.read())


def validate_imports(tree: ast.AST, allowed_imports: List):
    """validate the imports of the file

    Args:
        tree (ast.AST): the AST of the file
        allowed_imports (set): a set of allowed imports

    Raises:
        NotAllowedImportError: if an invalid import was found.
        None: if all imports are valid
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name in allowed_imports:
                    raise NotAllowedImportError(f"Import '{alias.name}' is not allowed")
        if isinstance(node, ast.ImportFrom):
            if node.module not in allowed_imports:
                raise NotAllowedImportError(f"Import '{node.module}' is not allowed")

def _execute_python_code(file_obj):
    """
    Executes Python code from a file-like object.
    Returns a list:
    [error_message (if any), namespace with executed code (if successful)].
    """
    result = [None, None]
    try:
        code = file_obj.read().decode()
        
        # Compile and execute the code
        compiled = compile(code, "<received_file>", "exec") 
        namespace = {}
        exec(compiled, namespace)
        result[1] = namespace  # Store the namespace if successful
    except (SyntaxError, Exception) as e:
        result[0] = str(e)  # Store the error message if an exception occurs
    
    return result


def extract_function(file_obj, func_name: str):
    """extracts a function from a file

    Args:
        file_obj (_type_): _description_
        func_name (str): function name to get extracted

    Returns:
        tuple: (error, function)
    """    

    error, namespace = _execute_python_code(file_obj)
    return error, namespace[func_name]


def convert_literal(test_cases):
    """convert a string representation of List/Tuple into a list[objects].

    Args:
        test_cases: [str]: string representation of objects to get converted
    Returns:
        list: list of converted datatypes
        False: if any errors occurred during conversion
    """
    try:
        obj =  ast.literal_eval(test_cases)
        if not isinstance(obj, tuple):
            obj = [obj]
        return obj
    except ValueError as e:
        print("ERROR WHILE CONVERTING LITERALS: ", e)
        return False