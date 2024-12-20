import ast
from .exceptions import NotAllowedImportError

def validate_imports(tree: ast.AST, allowed_imports: set):
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
