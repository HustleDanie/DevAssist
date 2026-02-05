"""
AST Transformers - Code transformation utilities for migration.

These transformers use the NodeTransformer pattern to automatically
convert deprecated patterns to their modern equivalents.
"""

import ast
from typing import Any


class Py2to3Transformer(ast.NodeTransformer):
    """
    AST transformer for Python 2 to Python 3 migration.
    
    This transformer handles common patterns:
    - xrange -> range
    - raw_input -> input
    - unicode -> str
    - print statements (via source manipulation)
    - dict.iteritems() -> dict.items()
    """

    def __init__(self) -> None:
        super().__init__()
        self.changes_made: list[str] = []

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Transform deprecated function calls."""
        self.generic_visit(node)

        if isinstance(node.func, ast.Name):
            # xrange -> range
            if node.func.id == "xrange":
                self.changes_made.append("xrange() -> range()")
                node.func.id = "range"
            
            # raw_input -> input
            elif node.func.id == "raw_input":
                self.changes_made.append("raw_input() -> input()")
                node.func.id = "input"
            
            # unicode -> str
            elif node.func.id == "unicode":
                self.changes_made.append("unicode() -> str()")
                node.func.id = "str"
            
            # long -> int
            elif node.func.id == "long":
                self.changes_made.append("long() -> int()")
                node.func.id = "int"

        # Handle dict.iteritems/iterkeys/itervalues
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "iteritems":
                self.changes_made.append(".iteritems() -> .items()")
                node.func.attr = "items"
            elif node.func.attr == "iterkeys":
                self.changes_made.append(".iterkeys() -> .keys()")
                node.func.attr = "keys"
            elif node.func.attr == "itervalues":
                self.changes_made.append(".itervalues() -> .values()")
                node.func.attr = "values"
            elif node.func.attr == "has_key":
                # dict.has_key(k) -> k in dict
                # This requires restructuring, return a Compare node
                self.changes_made.append(".has_key(k) -> k in dict")
                if node.args:
                    return ast.Compare(
                        left=node.args[0],
                        ops=[ast.In()],
                        comparators=[node.func.value]
                    )

        return node

    def visit_Import(self, node: ast.Import) -> ast.AST:
        """Transform renamed module imports."""
        renames = {
            "ConfigParser": "configparser",
            "Queue": "queue",
            "SocketServer": "socketserver",
            "repr": "reprlib",
            "Tkinter": "tkinter",
        }
        
        for alias in node.names:
            if alias.name in renames:
                old_name = alias.name
                alias.name = renames[alias.name]
                if alias.asname is None:
                    alias.asname = old_name  # Preserve old name for compatibility
                self.changes_made.append(f"import {old_name} -> import {alias.name}")
        
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Transform imports from renamed modules."""
        module_renames = {
            "ConfigParser": "configparser",
            "Queue": "queue",
            "SocketServer": "socketserver",
            "urllib2": "urllib.request",
            "urlparse": "urllib.parse",
            "StringIO": "io",
            "cStringIO": "io",
        }
        
        if node.module and node.module in module_renames:
            old_module = node.module
            node.module = module_renames[node.module]
            self.changes_made.append(f"from {old_module} -> from {node.module}")
        
        return node

    def transform(self, source: str) -> tuple[str, list[str]]:
        """
        Transform Python 2 source code to Python 3.
        
        Args:
            source: Python 2 source code
            
        Returns:
            Tuple of (transformed_source, list_of_changes)
        """
        self.changes_made = []
        
        try:
            tree = ast.parse(source)
            transformed_tree = self.visit(tree)
            ast.fix_missing_locations(transformed_tree)
            
            # Use ast.unparse (Python 3.9+) to get source back
            transformed_source = ast.unparse(transformed_tree)
            return transformed_source, self.changes_made
        except SyntaxError:
            # If we can't parse with AST, use regex-based fallback
            return self._transform_with_regex(source)
    
    def _transform_with_regex(self, source: str) -> tuple[str, list[str]]:
        """
        Fallback regex-based transformation for Python 2 syntax.
        
        Handles syntax that can't be AST-parsed by Python 3:
        - print statements: print "x" -> print("x")
        - except syntax: except E, e: -> except E as e:
        """
        import re
        changes = []
        transformed = source
        
        # First pass: Handle multi-line print statements
        # These end with an opening paren and continue on next lines
        # e.g., print "msg" % (
        #           arg1, arg2
        #       )
        # We need to find print statements where the content has unbalanced parens
        lines = transformed.split('\n')
        result_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for print statement (not already a function call)
            print_match = re.match(r'^(\s*)print\s+(?!\()(.+)$', line)
            if print_match:
                indent = print_match.group(1)
                content = print_match.group(2)
                
                # Check if this is a multi-line statement (unbalanced parens)
                paren_count = content.count('(') - content.count(')')
                
                if paren_count > 0:
                    # Multi-line print - collect continuation lines
                    full_content = content
                    while paren_count > 0 and i + 1 < len(lines):
                        i += 1
                        full_content += '\n' + lines[i]
                        paren_count += lines[i].count('(') - lines[i].count(')')
                    
                    # Handle trailing comma
                    if full_content.rstrip().endswith(','):
                        full_content = full_content.rstrip()[:-1]
                        result_lines.append(f"{indent}print({full_content}, end=' ')")
                    else:
                        result_lines.append(f"{indent}print({full_content})")
                    changes.append(f"print statement (multi-line) -> print()")
                else:
                    # Single-line print
                    # Handle >> redirect: print >> sys.stderr, "msg"
                    if content.strip().startswith('>>'):
                        redirect_match = re.match(r'>>\s*(\S+)\s*,\s*(.+)', content.strip())
                        if redirect_match:
                            file_obj = redirect_match.group(1)
                            msg = redirect_match.group(2)
                            result_lines.append(f'{indent}print({msg}, file={file_obj})')
                            changes.append(f"print >> file -> print(..., file=)")
                        else:
                            result_lines.append(line)
                    # Handle trailing comma (no newline): print "x",
                    elif content.rstrip().endswith(','):
                        content = content.rstrip()[:-1].strip()
                        result_lines.append(f'{indent}print({content}, end=\' \')')
                        changes.append(f"print trailing comma -> print(..., end=' ')")
                    else:
                        result_lines.append(f'{indent}print({content})')
                        changes.append(f"print statement -> print()")
            else:
                result_lines.append(line)
            i += 1
        
        transformed = '\n'.join(result_lines)
        
        # Transform except syntax: except Exception, e: -> except Exception as e:
        except_pattern = r'except\s+(\w+)\s*,\s*(\w+)\s*:'
        
        def replace_except(match):
            exc_type = match.group(1)
            var_name = match.group(2)
            changes.append(f"except {exc_type}, {var_name}: -> except {exc_type} as {var_name}:")
            return f'except {exc_type} as {var_name}:'
        
        transformed = re.sub(except_pattern, replace_except, transformed)
        
        # Transform unicode() -> str()
        unicode_pattern = r'\bunicode\s*\('
        if re.search(unicode_pattern, transformed):
            transformed = re.sub(unicode_pattern, 'str(', transformed)
            changes.append("unicode() -> str()")
        
        # Transform raw_input() -> input()
        raw_input_pattern = r'\braw_input\s*\('
        if re.search(raw_input_pattern, transformed):
            transformed = re.sub(raw_input_pattern, 'input(', transformed)
            changes.append("raw_input() -> input()")
        
        # Transform xrange() -> range()
        xrange_pattern = r'\bxrange\s*\('
        if re.search(xrange_pattern, transformed):
            transformed = re.sub(xrange_pattern, 'range(', transformed)
            changes.append("xrange() -> range()")
        
        # Transform long() -> int()
        long_pattern = r'\blong\s*\('
        if re.search(long_pattern, transformed):
            transformed = re.sub(long_pattern, 'int(', transformed)
            changes.append("long() -> int()")
        
        # Transform dict.iteritems() -> dict.items()
        if '.iteritems()' in transformed:
            transformed = transformed.replace('.iteritems()', '.items()')
            changes.append(".iteritems() -> .items()")
        
        if '.iterkeys()' in transformed:
            transformed = transformed.replace('.iterkeys()', '.keys()')
            changes.append(".iterkeys() -> .keys()")
        
        if '.itervalues()' in transformed:
            transformed = transformed.replace('.itervalues()', '.values()')
            changes.append(".itervalues() -> .values()")
        
        if '.has_key(' in transformed:
            # This is more complex, but do a simple replacement for now
            has_key_pattern = r'(\w+)\.has_key\(([^)]+)\)'
            transformed = re.sub(has_key_pattern, r'\2 in \1', transformed)
            changes.append(".has_key(k) -> k in dict")
        
        return transformed, changes


class FlaskToFastAPITransformer(ast.NodeTransformer):
    """
    AST transformer for Flask to FastAPI migration.
    
    This transformer handles:
    - Flask() -> FastAPI()
    - Blueprint() -> APIRouter()
    - @app.route() -> @app.get/post/etc()
    - Flask imports -> FastAPI imports
    - request.* -> FastAPI dependency injection
    """

    def __init__(self) -> None:
        super().__init__()
        self.changes_made: list[str] = []
        self.flask_app_name: str = "app"
        self.needs_pydantic_import = False
        self.route_info: list[dict[str, Any]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Transform Flask imports to FastAPI imports."""
        if node.module and "flask" in node.module.lower():
            new_imports: list[ast.alias] = []
            fastapi_imports: list[str] = []
            
            for alias in node.names:
                if alias.name == "Flask":
                    fastapi_imports.append("FastAPI")
                    self.changes_made.append("Flask -> FastAPI")
                elif alias.name == "Blueprint":
                    fastapi_imports.append("APIRouter")
                    self.changes_made.append("Blueprint -> APIRouter")
                elif alias.name == "request":
                    fastapi_imports.extend(["Request", "Depends"])
                    self.changes_made.append("request -> Request, Depends")
                elif alias.name == "jsonify":
                    # jsonify is not needed in FastAPI
                    self.changes_made.append("jsonify removed (not needed)")
                    continue
                elif alias.name == "redirect":
                    fastapi_imports.append("RedirectResponse")
                    self.changes_made.append("redirect -> RedirectResponse")
                elif alias.name == "abort":
                    fastapi_imports.append("HTTPException")
                    self.changes_made.append("abort -> HTTPException")
                else:
                    new_imports.append(alias)
            
            if fastapi_imports:
                # Create FastAPI import
                return ast.ImportFrom(
                    module="fastapi",
                    names=[ast.alias(name=n, asname=None) for n in fastapi_imports],
                    level=0
                )
            elif new_imports:
                node.names = new_imports
                return node
            else:
                # All imports were transformed, remove the node
                return None
        
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Transform Flask app creation."""
        self.generic_visit(node)
        
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                # Flask(__name__) -> FastAPI()
                if node.value.func.id == "Flask":
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.flask_app_name = target.id
                    
                    node.value.func.id = "FastAPI"
                    node.value.args = []  # FastAPI doesn't need __name__
                    self.changes_made.append("Flask(__name__) -> FastAPI()")
                
                # Blueprint('name', __name__) -> APIRouter()
                elif node.value.func.id == "Blueprint":
                    node.value.func.id = "APIRouter"
                    
                    # Extract prefix if provided
                    prefix = None
                    for keyword in node.value.keywords:
                        if keyword.arg == "url_prefix":
                            prefix = keyword
                            break
                    
                    node.value.args = []
                    node.value.keywords = []
                    if prefix:
                        node.value.keywords.append(
                            ast.keyword(arg="prefix", value=prefix.value)
                        )
                    
                    self.changes_made.append("Blueprint() -> APIRouter()")
        
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Transform Flask route functions."""
        new_decorators = []
        
        for decorator in node.decorator_list:
            transformed = self._transform_decorator(decorator, node)
            if transformed:
                new_decorators.append(transformed)
        
        node.decorator_list = new_decorators
        
        # Transform function body
        self.generic_visit(node)
        
        return node

    def _transform_decorator(
        self, decorator: ast.AST, func: ast.FunctionDef
    ) -> ast.AST | None:
        """Transform a Flask decorator to FastAPI."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == "route":
                    return self._transform_route_decorator(decorator)
        
        return decorator

    def _transform_route_decorator(self, decorator: ast.Call) -> ast.Call:
        """Transform @app.route() to @app.get/post/etc()."""
        # Extract path and methods
        path = decorator.args[0] if decorator.args else ast.Constant(value="/")
        methods = ["GET"]
        
        for keyword in decorator.keywords:
            if keyword.arg == "methods":
                if isinstance(keyword.value, ast.List):
                    methods = [
                        elt.value.upper() if isinstance(elt, ast.Constant) else "GET"
                        for elt in keyword.value.elts
                    ]
        
        # Use the first method (or create multiple decorators for multiple methods)
        method = methods[0].lower()
        
        self.changes_made.append(f"@route() -> @{method}()")
        
        return ast.Call(
            func=ast.Attribute(
                value=decorator.func.value,
                attr=method,
                ctx=ast.Load()
            ),
            args=[path],
            keywords=[]
        )

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Transform Flask function calls."""
        self.generic_visit(node)
        
        if isinstance(node.func, ast.Name):
            # jsonify(data) -> data (just return the dict)
            if node.func.id == "jsonify":
                self.changes_made.append("jsonify(x) -> x")
                if node.args:
                    return node.args[0]
                return ast.Dict(keys=[], values=[])
            
            # abort(404) -> raise HTTPException(status_code=404)
            if node.func.id == "abort":
                self.changes_made.append("abort(n) -> raise HTTPException(status_code=n)")
                return ast.Call(
                    func=ast.Name(id="HTTPException", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="status_code",
                            value=node.args[0] if node.args else ast.Constant(value=500)
                        )
                    ]
                )
        
        return node

    def transform(self, source: str) -> tuple[str, list[str]]:
        """
        Transform Flask source code to FastAPI.
        
        Args:
            source: Flask source code
            
        Returns:
            Tuple of (transformed_source, list_of_changes)
        """
        self.changes_made = []
        
        try:
            tree = ast.parse(source)
            transformed_tree = self.visit(tree)
            ast.fix_missing_locations(transformed_tree)
            transformed_source = ast.unparse(transformed_tree)
            return transformed_source, self.changes_made
        except SyntaxError:
            return source, []
