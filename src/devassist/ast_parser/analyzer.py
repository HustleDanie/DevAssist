"""
AST Analyzer - Core analysis engine for code inspection.

Uses Python's ast module to parse code and identify patterns that need
migration, with support for streaming results via generators.
"""

import ast
from typing import Generator
from pathlib import Path

from devassist.core.models import (
    MigrationType,
    DeprecatedPattern,
    CodeLocation,
)
from devassist.ast_parser.patterns import PatternMatcher


class ASTAnalyzer:
    """
    Analyzes Python source code using AST to identify migration patterns.
    
    This analyzer supports:
    - Python 2 to 3 migration patterns
    - Flask to FastAPI migration patterns
    - Custom pattern matching via PatternMatcher
    """

    def __init__(self) -> None:
        self.pattern_matcher = PatternMatcher()

    def analyze(
        self, source: str, migration_type: MigrationType
    ) -> Generator[DeprecatedPattern, None, None]:
        """
        Analyze source code for deprecated patterns.
        
        Args:
            source: Python source code as string
            migration_type: Type of migration to check for
            
        Yields:
            DeprecatedPattern objects for each identified issue
        """
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            # Try parsing as Python 2 if Python 3 parsing fails
            yield DeprecatedPattern(
                pattern_id="syntax_error",
                pattern_type="syntax_error",
                description=f"Syntax error (may indicate Python 2 code): {e.msg}",
                location=CodeLocation(
                    file_path=Path(""),
                    start_line=e.lineno or 1,
                    end_line=e.lineno or 1,
                ),
                original_code=source.split("\n")[e.lineno - 1] if e.lineno else "",
                severity="error",
            )
            return

        # Select the appropriate visitor based on migration type
        if migration_type == MigrationType.PY2_TO_PY3:
            yield from self._analyze_py2_patterns(tree, source)
        else:
            yield from self._analyze_flask_patterns(tree, source)

    def _analyze_py2_patterns(
        self, tree: ast.AST, source: str
    ) -> Generator[DeprecatedPattern, None, None]:
        """Analyze for Python 2 to 3 migration patterns."""
        visitor = Py2PatternVisitor(source)
        visitor.visit(tree)
        yield from visitor.patterns

    def _analyze_flask_patterns(
        self, tree: ast.AST, source: str
    ) -> Generator[DeprecatedPattern, None, None]:
        """Analyze for Flask to FastAPI migration patterns."""
        visitor = FlaskPatternVisitor(source)
        visitor.visit(tree)
        yield from visitor.patterns

    def analyze_file(
        self, file_path: Path, migration_type: MigrationType
    ) -> Generator[DeprecatedPattern, None, None]:
        """
        Analyze a file for deprecated patterns.
        
        Args:
            file_path: Path to the Python file
            migration_type: Type of migration
            
        Yields:
            DeprecatedPattern objects with file path set
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            for pattern in self.analyze(source, migration_type):
                pattern.location.file_path = file_path
                yield pattern
        except Exception as e:
            yield DeprecatedPattern(
                pattern_id="file_error",
                pattern_type="file_error",
                description=f"Error reading file: {str(e)}",
                location=CodeLocation(file_path=file_path, start_line=1, end_line=1),
                original_code="",
                severity="error",
            )


class Py2PatternVisitor(ast.NodeVisitor):
    """AST visitor to identify Python 2 patterns."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.lines = source.split("\n")
        self.patterns: list[DeprecatedPattern] = []
        self._pattern_count = 0

    def _get_source_segment(self, node: ast.AST) -> str:
        """Extract source code for a node."""
        try:
            return ast.get_source_segment(self.source, node) or ""
        except Exception:
            if hasattr(node, "lineno"):
                return self.lines[node.lineno - 1]
            return ""

    def _add_pattern(
        self, node: ast.AST, pattern_type: str, description: str, 
        severity: str = "warning", suggested_fix: str = ""
    ) -> None:
        """Add a pattern to the results."""
        self._pattern_count += 1
        self.patterns.append(DeprecatedPattern(
            pattern_id=f"ast_{self._pattern_count}",
            pattern_type=pattern_type,
            description=description,
            location=CodeLocation(
                file_path=Path(""),
                start_line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                start_col=getattr(node, "col_offset", 0),
                end_col=getattr(node, "end_col_offset", 0),
            ),
            original_code=self._get_source_segment(node),
            severity=severity,
            suggested_fix=suggested_fix,
        ))

    def visit_Call(self, node: ast.Call) -> None:
        """Check for deprecated function calls."""
        # Check for print as a function (might still have issues)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # xrange -> range
            if func_name == "xrange":
                self._add_pattern(
                    node, "xrange_usage",
                    "xrange() is not available in Python 3",
                    suggested_fix="Replace xrange() with range()"
                )
            
            # raw_input -> input
            elif func_name == "raw_input":
                self._add_pattern(
                    node, "raw_input_usage",
                    "raw_input() is not available in Python 3",
                    suggested_fix="Replace raw_input() with input()"
                )
            
            # execfile is removed
            elif func_name == "execfile":
                self._add_pattern(
                    node, "execfile_usage",
                    "execfile() is not available in Python 3",
                    severity="error",
                    suggested_fix="Use exec(open(file).read()) instead"
                )
            
            # unicode -> str
            elif func_name == "unicode":
                self._add_pattern(
                    node, "unicode_usage",
                    "unicode() is not available in Python 3",
                    suggested_fix="Replace unicode() with str()"
                )
            
            # long -> int
            elif func_name == "long":
                self._add_pattern(
                    node, "long_usage",
                    "long() is not available in Python 3",
                    suggested_fix="Replace long() with int()"
                )

        # Check for dict.iteritems(), dict.iterkeys(), dict.itervalues()
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if method_name in ("iteritems", "iterkeys", "itervalues"):
                self._add_pattern(
                    node, f"{method_name}_usage",
                    f"dict.{method_name}() is not available in Python 3",
                    suggested_fix=f"Replace .{method_name}() with .{method_name[4:]}()"
                )
            
            # has_key -> in operator
            if method_name == "has_key":
                self._add_pattern(
                    node, "has_key_usage",
                    "dict.has_key() is not available in Python 3",
                    suggested_fix="Use 'key in dict' instead"
                )

        self.generic_visit(node)

    def visit_Print(self, node: ast.AST) -> None:
        """Check for print statements (Python 2 style)."""
        # This won't be triggered in Python 3 AST, but included for completeness
        self._add_pattern(
            node, "print_statement",
            "print statement is not valid in Python 3",
            suggested_fix="Use print() function instead"
        )
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        """Check for old-style raise statements."""
        # In Python 2: raise E, V, T
        # In Python 3: raise E(V).with_traceback(T)
        if hasattr(node, "type") and hasattr(node, "inst"):
            # Old style raise
            self._add_pattern(
                node, "old_raise_syntax",
                "Old-style raise syntax",
                suggested_fix="Use 'raise Exception(args)' syntax"
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Check for old-style except syntax."""
        # The old syntax `except E, e:` becomes `except E as e:`
        # Python 3 AST uses 'name' attribute, not 'as' syntax issue detectable here
        # Check if there's a comma in the source line (heuristic)
        if node.name and node.lineno:
            line = self.lines[node.lineno - 1]
            if "," in line and " as " not in line.lower():
                self._add_pattern(
                    node, "old_except_syntax",
                    "Old-style except syntax with comma",
                    suggested_fix="Use 'except Exception as e:' syntax"
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Check for renamed/removed modules."""
        py2_modules = {
            "ConfigParser": "configparser",
            "Queue": "queue",
            "SocketServer": "socketserver",
            "repr": "reprlib",
            "tkFileDialog": "tkinter.filedialog",
            "Tkinter": "tkinter",
        }
        
        for alias in node.names:
            if alias.name in py2_modules:
                self._add_pattern(
                    node, "renamed_module",
                    f"Module '{alias.name}' is renamed in Python 3",
                    suggested_fix=f"Use '{py2_modules[alias.name]}' instead"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for imports from renamed/removed modules."""
        if node.module:
            py2_modules = {
                "ConfigParser": "configparser",
                "Queue": "queue",
                "SocketServer": "socketserver",
                "urllib2": "urllib.request",
                "urlparse": "urllib.parse",
                "StringIO": "io",
                "cStringIO": "io",
            }
            
            if node.module in py2_modules:
                self._add_pattern(
                    node, "renamed_module_import",
                    f"Module '{node.module}' is renamed/moved in Python 3",
                    suggested_fix=f"Import from '{py2_modules[node.module]}' instead"
                )
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Check for division behavior changes."""
        # Classic division / vs floor division //
        # This is a heuristic - true division is the default in Python 3
        if isinstance(node.op, ast.Div):
            # Check if operands are likely integers
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, int):
                if isinstance(node.right, ast.Constant) and isinstance(node.right.value, int):
                    self._add_pattern(
                        node, "division_behavior",
                        "Integer division behavior differs in Python 3",
                        severity="info",
                        suggested_fix="Use // for integer division, / for true division"
                    )
        self.generic_visit(node)


class FlaskPatternVisitor(ast.NodeVisitor):
    """AST visitor to identify Flask patterns for FastAPI migration."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.lines = source.split("\n")
        self.patterns: list[DeprecatedPattern] = []
        self._pattern_count = 0
        self._flask_app_names: set[str] = set()

    def _get_source_segment(self, node: ast.AST) -> str:
        """Extract source code for a node."""
        try:
            return ast.get_source_segment(self.source, node) or ""
        except Exception:
            if hasattr(node, "lineno"):
                return self.lines[node.lineno - 1]
            return ""

    def _add_pattern(
        self, node: ast.AST, pattern_type: str, description: str,
        severity: str = "warning", suggested_fix: str = ""
    ) -> None:
        """Add a pattern to the results."""
        self._pattern_count += 1
        self.patterns.append(DeprecatedPattern(
            pattern_id=f"flask_{self._pattern_count}",
            pattern_type=pattern_type,
            description=description,
            location=CodeLocation(
                file_path=Path(""),
                start_line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                start_col=getattr(node, "col_offset", 0),
                end_col=getattr(node, "end_col_offset", 0),
            ),
            original_code=self._get_source_segment(node),
            severity=severity,
            suggested_fix=suggested_fix,
        ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for Flask imports."""
        if node.module and "flask" in node.module.lower():
            imports = [alias.name for alias in node.names]
            
            if "Flask" in imports:
                self._add_pattern(
                    node, "flask_import",
                    "Flask application import",
                    severity="info",
                    suggested_fix="Replace with 'from fastapi import FastAPI'"
                )
            
            if "request" in imports:
                self._add_pattern(
                    node, "flask_request_import",
                    "Flask request object import",
                    suggested_fix="Use FastAPI dependency injection instead"
                )
            
            if "Blueprint" in imports:
                self._add_pattern(
                    node, "flask_blueprint_import",
                    "Flask Blueprint import",
                    suggested_fix="Replace with 'from fastapi import APIRouter'"
                )
            
            if "jsonify" in imports:
                self._add_pattern(
                    node, "flask_jsonify_import",
                    "Flask jsonify import",
                    suggested_fix="FastAPI returns JSON by default, remove jsonify"
                )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track Flask app instantiation."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id == "Flask":
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self._flask_app_names.add(target.id)
                            self._add_pattern(
                                node, "flask_app_creation",
                                f"Flask app instantiation: {target.id}",
                                severity="info",
                                suggested_fix="Replace with 'app = FastAPI()'"
                            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check for Flask route decorators and patterns."""
        for decorator in node.decorator_list:
            self._check_route_decorator(decorator, node)
        
        # Check for Flask-specific patterns in function body
        for child in ast.walk(node):
            self._check_flask_patterns_in_function(child, node)
        
        self.generic_visit(node)

    def _check_route_decorator(self, decorator: ast.AST, func: ast.FunctionDef) -> None:
        """Check if decorator is a Flask route."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == "route":
                    # @app.route(...)
                    methods = self._extract_methods(decorator)
                    suggested = self._suggest_fastapi_decorator(methods)
                    self._add_pattern(
                        decorator, "flask_route_decorator",
                        f"Flask @route decorator on {func.name}()",
                        suggested_fix=suggested
                    )
                elif decorator.func.attr in ("get", "post", "put", "delete", "patch"):
                    # Already using specific method decorators (rare in Flask)
                    self._add_pattern(
                        decorator, "flask_method_decorator",
                        f"Flask @{decorator.func.attr} decorator",
                        severity="info",
                        suggested_fix=f"Update to FastAPI @app.{decorator.func.attr}() with path parameters"
                    )

    def _extract_methods(self, decorator: ast.Call) -> list[str]:
        """Extract HTTP methods from @route decorator."""
        methods = ["GET"]  # Default
        for keyword in decorator.keywords:
            if keyword.arg == "methods":
                if isinstance(keyword.value, ast.List):
                    methods = [
                        elt.value.upper() if isinstance(elt, ast.Constant) else "GET"
                        for elt in keyword.value.elts
                    ]
        return methods

    def _suggest_fastapi_decorator(self, methods: list[str]) -> str:
        """Suggest FastAPI decorator based on HTTP methods."""
        if len(methods) == 1:
            method = methods[0].lower()
            return f"Use @app.{method}('/path') decorator"
        return f"Split into multiple routes: @app.{', @app.'.join(m.lower() for m in methods)}()"

    def _check_flask_patterns_in_function(self, node: ast.AST, func: ast.FunctionDef) -> None:
        """Check for Flask-specific patterns in function body."""
        if isinstance(node, ast.Attribute):
            # request.form, request.args, request.json, etc.
            if isinstance(node.value, ast.Name) and node.value.id == "request":
                if node.attr in ("form", "args", "json", "files", "cookies"):
                    self._add_pattern(
                        node, f"flask_request_{node.attr}",
                        f"Flask request.{node.attr} usage in {func.name}()",
                        suggested_fix=f"Use FastAPI dependency injection or Pydantic models"
                    )
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # jsonify() call
                if node.func.id == "jsonify":
                    self._add_pattern(
                        node, "flask_jsonify_call",
                        f"Flask jsonify() call in {func.name}()",
                        suggested_fix="Return dict or Pydantic model directly"
                    )
                # render_template() call
                elif node.func.id == "render_template":
                    self._add_pattern(
                        node, "flask_render_template",
                        f"Flask render_template() call in {func.name}()",
                        suggested_fix="Use FastAPI Jinja2Templates or return HTML response"
                    )
                # redirect() call
                elif node.func.id == "redirect":
                    self._add_pattern(
                        node, "flask_redirect",
                        f"Flask redirect() call in {func.name}()",
                        suggested_fix="Use FastAPI RedirectResponse"
                    )
                # abort() call
                elif node.func.id == "abort":
                    self._add_pattern(
                        node, "flask_abort",
                        f"Flask abort() call in {func.name}()",
                        suggested_fix="Raise HTTPException instead"
                    )
