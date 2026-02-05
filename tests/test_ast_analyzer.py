"""Tests for AST analyzer module."""

import pytest
from pathlib import Path

from devassist.ast_parser.analyzer import ASTAnalyzer, Py2PatternVisitor, FlaskPatternVisitor
from devassist.core.models import MigrationType


class TestASTAnalyzer:
    """Tests for the ASTAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ASTAnalyzer()

    def test_analyze_py2_xrange(self):
        """Test detection of xrange usage."""
        source = """
for i in xrange(10):
    print(i)
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        xrange_patterns = [p for p in patterns if "xrange" in p.pattern_type]
        assert len(xrange_patterns) >= 1
        assert xrange_patterns[0].severity == "warning"

    def test_analyze_py2_raw_input(self):
        """Test detection of raw_input usage."""
        source = """
name = raw_input("Enter your name: ")
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        raw_input_patterns = [p for p in patterns if "raw_input" in p.pattern_type]
        assert len(raw_input_patterns) >= 1

    def test_analyze_py2_dict_iteritems(self):
        """Test detection of dict.iteritems usage."""
        source = """
d = {'a': 1, 'b': 2}
for k, v in d.iteritems():
    print(k, v)
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        iter_patterns = [p for p in patterns if "iteritems" in p.pattern_type]
        assert len(iter_patterns) >= 1

    def test_analyze_flask_route(self):
        """Test detection of Flask route decorators."""
        source = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify([])
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.FLASK_TO_FASTAPI))
        
        route_patterns = [p for p in patterns if "route" in p.pattern_type.lower()]
        assert len(route_patterns) >= 1

    def test_analyze_flask_imports(self):
        """Test detection of Flask imports."""
        source = """
from flask import Flask, request, jsonify, Blueprint
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.FLASK_TO_FASTAPI))
        
        import_patterns = [p for p in patterns if "import" in p.pattern_type]
        assert len(import_patterns) >= 1

    def test_analyze_syntax_error(self):
        """Test handling of syntax errors."""
        source = """
def broken(
    # Missing closing paren
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        # Should return a syntax error pattern
        error_patterns = [p for p in patterns if p.severity == "error"]
        assert len(error_patterns) >= 1

    def test_analyze_empty_source(self):
        """Test analysis of empty source code."""
        source = ""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        # Empty source should have no patterns
        assert len(patterns) == 0

    def test_analyze_valid_py3_code(self):
        """Test that valid Python 3 code has minimal patterns."""
        source = """
def greet(name: str) -> str:
    return f"Hello, {name}!"

for i in range(10):
    print(greet(f"User {i}"))
"""
        patterns = list(self.analyzer.analyze(source, MigrationType.PY2_TO_PY3))
        
        # Valid Python 3 code should have few or no issues
        error_patterns = [p for p in patterns if p.severity == "error"]
        assert len(error_patterns) == 0


class TestPy2PatternVisitor:
    """Tests for the Py2PatternVisitor class."""

    def test_visit_call_xrange(self):
        """Test xrange detection in Call visitor."""
        source = "result = xrange(100)"
        visitor = Py2PatternVisitor(source)
        
        import ast
        tree = ast.parse(source)
        visitor.visit(tree)
        
        assert len(visitor.patterns) >= 1
        assert any("xrange" in p.pattern_type for p in visitor.patterns)

    def test_visit_import_renamed_module(self):
        """Test renamed module import detection."""
        source = "import ConfigParser"
        visitor = Py2PatternVisitor(source)
        
        import ast
        tree = ast.parse(source)
        visitor.visit(tree)
        
        assert len(visitor.patterns) >= 1
        assert any("renamed_module" in p.pattern_type for p in visitor.patterns)


class TestFlaskPatternVisitor:
    """Tests for the FlaskPatternVisitor class."""

    def test_visit_flask_app_creation(self):
        """Test Flask app creation detection."""
        source = """
from flask import Flask
app = Flask(__name__)
"""
        visitor = FlaskPatternVisitor(source)
        
        import ast
        tree = ast.parse(source)
        visitor.visit(tree)
        
        app_patterns = [p for p in visitor.patterns if "flask_app" in p.pattern_type]
        assert len(app_patterns) >= 1

    def test_visit_jsonify_call(self):
        """Test jsonify call detection."""
        source = """
def endpoint():
    return jsonify({'status': 'ok'})
"""
        visitor = FlaskPatternVisitor(source)
        
        import ast
        tree = ast.parse(source)
        visitor.visit(tree)
        
        jsonify_patterns = [p for p in visitor.patterns if "jsonify" in p.pattern_type]
        assert len(jsonify_patterns) >= 1
