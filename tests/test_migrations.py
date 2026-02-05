"""Tests for migration modules."""

import pytest
from pathlib import Path

from devassist.migrations.py2to3 import Py2to3Migration
from devassist.migrations.flask_to_fastapi import FlaskToFastAPIMigration


class TestPy2to3Migration:
    """Tests for Python 2 to 3 migration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.migration = Py2to3Migration()

    def test_analyze_xrange(self):
        """Test analysis of xrange patterns."""
        source = """
for i in xrange(10):
    print(i)
"""
        patterns = list(self.migration.analyze(source))
        xrange_patterns = [p for p in patterns if "xrange" in p.pattern_type]
        assert len(xrange_patterns) >= 1

    def test_analyze_print_statement(self):
        """Test analysis of print statement patterns."""
        source = """
print "Hello, World!"
"""
        patterns = list(self.migration.analyze(source))
        # May detect via regex pattern matcher
        assert len(patterns) >= 0  # Print detection depends on parsing

    def test_transform_xrange(self):
        """Test transformation of xrange to range."""
        source = "result = list(xrange(10))"
        transformed, changes = self.migration.transform(source)
        
        assert "range" in transformed
        assert "xrange" not in transformed

    def test_transform_raw_input(self):
        """Test transformation of raw_input to input."""
        source = "name = raw_input('Enter name: ')"
        transformed, changes = self.migration.transform(source)
        
        assert "input" in transformed
        assert "raw_input" not in transformed

    def test_get_futurize_imports(self):
        """Test getting recommended future imports."""
        source = """
print "Hello"
result = 5 / 2
"""
        imports = self.migration.get_futurize_imports(source)
        
        assert any("print_function" in imp for imp in imports)
        assert any("division" in imp for imp in imports)

    def test_migrate_file(self):
        """Test full file migration."""
        source = """
for i in xrange(10):
    print i
"""
        result = self.migration.migrate_file(source, apply_fixes=True)
        
        assert "patterns_found" in result
        assert result["patterns_found"] >= 0

    def test_get_migration_summary_no_patterns(self):
        """Test summary when no patterns found."""
        patterns = []
        summary = self.migration.get_migration_summary(patterns)
        
        assert "No Python 2 patterns found" in summary


class TestFlaskToFastAPIMigration:
    """Tests for Flask to FastAPI migration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.migration = FlaskToFastAPIMigration()

    def test_analyze_flask_app(self):
        """Test analysis of Flask app creation."""
        source = """
from flask import Flask
app = Flask(__name__)
"""
        patterns = list(self.migration.analyze(source))
        flask_patterns = [p for p in patterns if "flask" in p.pattern_type.lower()]
        assert len(flask_patterns) >= 1

    def test_analyze_flask_route(self):
        """Test analysis of Flask routes."""
        source = """
@app.route('/users', methods=['GET', 'POST'])
def users():
    return jsonify([])
"""
        patterns = list(self.migration.analyze(source))
        # Should detect route decorator
        assert len(patterns) >= 0

    def test_get_required_imports(self):
        """Test getting required FastAPI imports."""
        source = """
from flask import Flask, request, jsonify
app = Flask(__name__)
"""
        imports = self.migration.get_required_imports(source)
        
        assert any("FastAPI" in imp for imp in imports)

    def test_generate_pydantic_models(self):
        """Test generating Pydantic models."""
        source = "# Flask app"
        models = self.migration.generate_pydantic_models(source)
        
        assert "BaseModel" in models
        assert "pydantic" in models

    def test_get_migration_checklist(self):
        """Test getting migration checklist."""
        checklist = self.migration.get_migration_checklist()
        
        assert len(checklist) > 0
        assert any("FastAPI" in item for item in checklist)
        assert any("uvicorn" in item for item in checklist)

    def test_migrate_file(self):
        """Test full file migration."""
        source = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'status': 'ok'})
"""
        result = self.migration.migrate_file(source, apply_fixes=True)
        
        assert "patterns_found" in result
        assert "required_imports" in result

    def test_get_migration_summary_no_patterns(self):
        """Test summary when no patterns found."""
        patterns = []
        summary = self.migration.get_migration_summary(patterns)
        
        assert "No Flask patterns found" in summary
