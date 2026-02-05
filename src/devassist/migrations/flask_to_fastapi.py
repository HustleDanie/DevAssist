"""
Flask to FastAPI Migration - Specific migration patterns and rules.

This module provides comprehensive migration support for converting
Flask applications to FastAPI, handling route definitions, request/response
handling, and middleware patterns.
"""

from dataclasses import dataclass
from typing import Generator

from devassist.ast_parser import ASTAnalyzer, FlaskToFastAPITransformer, PatternMatcher
from devassist.core.models import (
    MigrationType,
    DeprecatedPattern,
    CodeChange,
)


@dataclass
class FastAPIEquivalent:
    """Mapping from Flask pattern to FastAPI equivalent."""
    
    flask_pattern: str
    fastapi_equivalent: str
    description: str
    requires_import: list[str]
    example_before: str
    example_after: str


class FlaskToFastAPIMigration:
    """
    Handles Flask to FastAPI migration.
    
    Supported migrations:
    - Route decorators (@app.route -> @app.get/post/etc)
    - Request handling (Flask request -> FastAPI dependency injection)
    - Response handling (jsonify -> direct return)
    - Blueprint -> APIRouter
    - Error handling (abort -> HTTPException)
    - Middleware patterns
    - Template rendering
    """

    def __init__(self) -> None:
        self.analyzer = ASTAnalyzer()
        self.transformer = FlaskToFastAPITransformer()
        self.pattern_matcher = PatternMatcher()
        self.equivalents = self._build_equivalents()

    def _build_equivalents(self) -> list[FastAPIEquivalent]:
        """Build the list of Flask to FastAPI equivalents."""
        return [
            FastAPIEquivalent(
                flask_pattern="Flask(__name__)",
                fastapi_equivalent="FastAPI()",
                description="Application instantiation",
                requires_import=["from fastapi import FastAPI"],
                example_before="app = Flask(__name__)",
                example_after="app = FastAPI()"
            ),
            FastAPIEquivalent(
                flask_pattern="@app.route('/', methods=['GET'])",
                fastapi_equivalent="@app.get('/')",
                description="GET route decorator",
                requires_import=[],
                example_before="@app.route('/users', methods=['GET'])\ndef get_users():",
                example_after="@app.get('/users')\nasync def get_users():"
            ),
            FastAPIEquivalent(
                flask_pattern="@app.route('/', methods=['POST'])",
                fastapi_equivalent="@app.post('/')",
                description="POST route decorator",
                requires_import=[],
                example_before="@app.route('/users', methods=['POST'])\ndef create_user():",
                example_after="@app.post('/users')\nasync def create_user(user: UserCreate):"
            ),
            FastAPIEquivalent(
                flask_pattern="request.json",
                fastapi_equivalent="Pydantic model parameter",
                description="JSON request body",
                requires_import=["from pydantic import BaseModel"],
                example_before="data = request.json",
                example_after="async def endpoint(data: DataModel):"
            ),
            FastAPIEquivalent(
                flask_pattern="request.args",
                fastapi_equivalent="Query parameters",
                description="Query string parameters",
                requires_import=["from fastapi import Query"],
                example_before="name = request.args.get('name')",
                example_after="async def endpoint(name: str = Query(None)):"
            ),
            FastAPIEquivalent(
                flask_pattern="request.form",
                fastapi_equivalent="Form parameters",
                description="Form data",
                requires_import=["from fastapi import Form"],
                example_before="name = request.form['name']",
                example_after="async def endpoint(name: str = Form(...)):"
            ),
            FastAPIEquivalent(
                flask_pattern="jsonify(data)",
                fastapi_equivalent="return data",
                description="JSON response",
                requires_import=[],
                example_before="return jsonify({'status': 'ok'})",
                example_after="return {'status': 'ok'}"
            ),
            FastAPIEquivalent(
                flask_pattern="Blueprint",
                fastapi_equivalent="APIRouter",
                description="Route grouping",
                requires_import=["from fastapi import APIRouter"],
                example_before="bp = Blueprint('users', __name__)",
                example_after="router = APIRouter(prefix='/users')"
            ),
            FastAPIEquivalent(
                flask_pattern="abort(404)",
                fastapi_equivalent="raise HTTPException(status_code=404)",
                description="HTTP error response",
                requires_import=["from fastapi import HTTPException"],
                example_before="abort(404)",
                example_after="raise HTTPException(status_code=404, detail='Not found')"
            ),
            FastAPIEquivalent(
                flask_pattern="@app.before_request",
                fastapi_equivalent="Middleware or Depends",
                description="Pre-request processing",
                requires_import=["from fastapi import Depends"],
                example_before="@app.before_request\ndef before():",
                example_after="async def dependency():\n    # pre-processing\n\n@app.get('/', dependencies=[Depends(dependency)])"
            ),
        ]

    def analyze(self, source: str) -> Generator[DeprecatedPattern, None, None]:
        """
        Analyze source code for Flask patterns.
        
        Args:
            source: Python source code
            
        Yields:
            DeprecatedPattern for each Flask pattern found
        """
        yield from self.analyzer.analyze(source, MigrationType.FLASK_TO_FASTAPI)

    def transform(self, source: str) -> tuple[str, list[CodeChange]]:
        """
        Transform Flask source to FastAPI.
        
        Args:
            source: Flask source code
            
        Returns:
            Tuple of (transformed_code, list_of_changes)
        """
        transformed, changes_list = self.transformer.transform(source)
        
        changes: list[CodeChange] = []
        for i, change_desc in enumerate(changes_list):
            changes.append(CodeChange(
                change_id=f"flask_to_fastapi_{i}",
                pattern_id=f"transform_{i}",
                file_path="",
                original_code="",
                new_code="",
                start_line=0,
                end_line=0,
                explanation=change_desc,
            ))
        
        return transformed, changes

    def get_required_imports(self, source: str) -> list[str]:
        """
        Determine required FastAPI imports based on Flask patterns.
        
        Args:
            source: Source code to analyze
            
        Returns:
            List of required import statements
        """
        imports = set()
        imports.add("from fastapi import FastAPI")
        
        patterns = list(self.analyze(source))
        
        for pattern in patterns:
            if "request" in pattern.pattern_type:
                imports.add("from fastapi import Request, Depends")
            if "blueprint" in pattern.pattern_type.lower():
                imports.add("from fastapi import APIRouter")
            if "abort" in pattern.pattern_type:
                imports.add("from fastapi import HTTPException")
            if "form" in pattern.pattern_type:
                imports.add("from fastapi import Form")
            if "json" in pattern.pattern_type:
                imports.add("from pydantic import BaseModel")
        
        return sorted(imports)

    def generate_pydantic_models(self, source: str) -> str:
        """
        Generate Pydantic models for request/response validation.
        
        Args:
            source: Flask source code
            
        Returns:
            Generated Pydantic model definitions
        """
        # This would analyze the Flask code to determine
        # what data structures are being used and generate
        # appropriate Pydantic models
        
        models = '''"""Auto-generated Pydantic models for FastAPI migration."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: str = ""


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    code: Optional[str] = None


# Add your domain models below
# Example:
# class UserCreate(BaseModel):
#     username: str = Field(..., min_length=3, max_length=50)
#     email: str
#     password: str = Field(..., min_length=8)
'''
        return models

    def migrate_file(
        self, source: str, apply_fixes: bool = True
    ) -> dict:
        """
        Perform complete migration analysis and optionally apply fixes.
        
        Args:
            source: Source code to migrate
            apply_fixes: Whether to apply automatic fixes
            
        Returns:
            Dictionary with migration results
        """
        patterns = list(self.analyze(source))
        
        # Categorize patterns
        categories = {
            "routing": [],
            "request_handling": [],
            "response_handling": [],
            "imports": [],
            "other": [],
        }
        
        for pattern in patterns:
            if "route" in pattern.pattern_type:
                categories["routing"].append(pattern)
            elif "request" in pattern.pattern_type:
                categories["request_handling"].append(pattern)
            elif "response" in pattern.pattern_type or "jsonify" in pattern.pattern_type:
                categories["response_handling"].append(pattern)
            elif "import" in pattern.pattern_type:
                categories["imports"].append(pattern)
            else:
                categories["other"].append(pattern)
        
        result = {
            "patterns_found": len(patterns),
            "by_category": {k: len(v) for k, v in categories.items()},
            "patterns": patterns,
            "required_imports": self.get_required_imports(source),
        }
        
        if apply_fixes:
            transformed, changes = self.transform(source)
            result["transformed"] = transformed
            result["changes"] = changes
            result["changes_applied"] = len(changes)
            result["pydantic_models"] = self.generate_pydantic_models(source)
        
        return result

    def get_migration_checklist(self) -> list[str]:
        """
        Get a checklist of manual steps for Flask to FastAPI migration.
        
        Returns:
            List of checklist items
        """
        return [
            "Install FastAPI dependencies: pip install fastapi uvicorn",
            "Replace Flask app with FastAPI app",
            "Convert route decorators to specific HTTP methods",
            "Create Pydantic models for request/response validation",
            "Replace request.json with Pydantic model parameters",
            "Replace request.args with Query parameters",
            "Replace request.form with Form parameters",
            "Replace jsonify() with direct dict/model returns",
            "Replace abort() with HTTPException",
            "Convert Blueprints to APIRouters",
            "Update middleware patterns",
            "Replace Flask-specific extensions",
            "Update CORS configuration",
            "Update authentication/authorization",
            "Add async/await where beneficial",
            "Update tests to use TestClient",
            "Update deployment (gunicorn -> uvicorn)",
            "Review and update documentation",
        ]

    def get_migration_summary(self, patterns: list[DeprecatedPattern]) -> str:
        """
        Generate a human-readable summary of required migrations.
        
        Args:
            patterns: List of patterns found
            
        Returns:
            Summary string
        """
        if not patterns:
            return "No Flask patterns found. Code may already be using FastAPI."
        
        lines = [f"Found {len(patterns)} Flask patterns that need migration:\n"]
        
        by_type: dict[str, int] = {}
        for pattern in patterns:
            by_type[pattern.pattern_type] = by_type.get(pattern.pattern_type, 0) + 1
        
        for ptype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  - {ptype}: {count} occurrences")
        
        lines.append("\nKey migration steps:")
        lines.append("  1. Install FastAPI: pip install fastapi uvicorn")
        lines.append("  2. Create Pydantic models for data validation")
        lines.append("  3. Run automated transformation")
        lines.append("  4. Review async/await opportunities")
        lines.append("  5. Update tests to use FastAPI TestClient")
        
        return "\n".join(lines)
