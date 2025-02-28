import ast

# import re
from typing import List
from fastapi import HTTPException, UploadFile


def func_error(func_name: str, line_number: int):
    return f"VALIDATION ERROR line {line_number}: use of function '{func_name}' is not allowed."


class PythonFile:
    def __init__(self, upload_file: UploadFile, allowed_imports: List):
        self.file = upload_file.file
        self.allowed_imports = allowed_imports
        self.source_code = self.get_source_code()
        print(self.source_code)

    def get_source_code(self):
        return self.file.read().decode("utf-8")

    def validate(self):
        """
        Validate the python file.

        Checks for:
        1. any syntax errors
        2. any invalid imports
        3. any invalid functions

        Returns:
            tuple: (bool, str) where bool is True if the file is valid, False otherwise.
                str is an error message if the file is invalid, None otherwise
        """
        # check for any syntax errors
        try:
            tree = ast.parse(source=self.source_code)
        except (SyntaxError, Exception) as e:
            return False, f"VALIDATION ERROR: {str(e)}"

        invalid_functions = set({"compile", "eval", "exec"})
        for node in ast.walk(tree):
            # check for invalid imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not alias.name in self.allowed_imports:
                        return (
                            False,
                            f"VALIDATION ERROR: Import '{alias.name}' is not allowed.",
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module not in self.allowed_imports:
                    return (
                        False,
                        f"VALIDATION ERROR: Import '{node.module}' is not allowed.",
                    )

            # check for invalid functions
            elif (
                isinstance(node, ast.Name) and node.id in invalid_functions
            ):  # 'compile'
                return False, func_error(node.id, node.lineno)
            elif isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in invalid_functions
                ):  # 'compile()'
                    return False, func_error(node.func.id, node.lineno)
                elif isinstance(node.func, ast.Attribute):  # module.compile()
                    if node.func.attr in invalid_functions:
                        return False, func_error(node.func.attr, node.lineno)
            elif isinstance(node, ast.Attribute):  # module.compile
                if node.attr in invalid_functions:
                    return False, func_error(node.attr, node.lineno)
        return True, None

    def _execute_python_code(self):
        """
        Executes Python code from a string.
        Returns a list:
        [error_message (if any), namespace with executed code (if successful)].
        """
        result = [None, None]
        try:
            # Compile and execute the code
            compiled = compile(self.source_code, "<received_file>", "exec")
            namespace = {}
            exec(compiled, namespace)
            result[1] = namespace
        except (SyntaxError, Exception) as e:
            result[0] = str(e)
        return result

    def extract_function(self, func_name: str):
        """extracts a function from a python source code

        Args:
            func_name (str): function name to get extracted

        Returns:
            None: if the function is not found
            function: if the function is found
        """

        error, namespace = self._execute_python_code()
        if error or not namespace:
            return None

        func = namespace.get(func_name)
        return func


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
                    raise HTTPException(
                        422, f"VALIDATION ERROR: Import '{alias.name}' is not allowed"
                    )
        if isinstance(node, ast.ImportFrom):
            if node.module not in allowed_imports:
                raise HTTPException(
                    422, f"VALIDATION ERROR: Import '{node.module}' is not allowed"
                )


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


def evaluate_dict_values(dictionary: dict):
    """if the values of a dictionary is in string format convert's it to its actual type

    Args:
        dictionary (dict): example: {'id': 1, 'input': '[1, 3]', 'expected': '(3, 3)'}

    Returns:
        dictionary (dict): example: {'id': 1, 'input': [1, 3], 'expected': (3, 3)}
    """
    if not isinstance(dictionary, dict):
        raise ValueError("invalid format please provide a dictionary")
    for key, val in dictionary.items():
        if isinstance(val, str):
            dictionary[key] = ast.literal_eval(val)
    return dictionary


def convert_literal(test_cases):
    """convert a string representation of List/Tuple into a list[objects].

    Args:
        test_cases: [str]: string representation of objects to get converted
    Returns:
        list: list of converted datatypes
        False: if any errors occurred during conversion
    """
    obj = ast.literal_eval(test_cases)

    if isinstance(obj, dict):
        return [evaluate_dict_values(obj)]

    # obj will look like this: [{'id': 1, 'input': '[2, 7, 11, 15], 9', 'expected': '[0, 1]'},
    #                           {'id': 2, 'input': '[3, 2, 4], 6', 'expected': '[1, 2]'}]
    # as you see here the input/expected are in string format and we dont want that
    # down below we are converting those:
    testcases = []
    for testcase in obj:
        new_testcase = testcase.copy()
        for key in testcase:
            if key == "input" or key == "expected" and isinstance(testcase[key], str):
                # print("testcase[key]: ", testcase[key], type(testcase[key]))
                new_testcase[key] = ast.literal_eval(testcase[key])
        testcases.append(new_testcase)
    return testcases


if __name__ == "__main__":
    result = convert_literal(
        "{'id': 1, 'input': '[2, 7, 11, 15], 9', 'expected': '[0, 1]'}"
    )
    print(f"final result: {result}")
