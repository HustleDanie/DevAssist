"""
MCP Server - Local MCP server for DevAssist.

This server provides documentation context to the migration agents,
including style guides, migration patterns, and code examples.
"""

import json
from pathlib import Path
from typing import Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MCP server."""

    # Class-level storage for documentation
    style_guides: dict[str, str] = {}
    migration_guides: dict[str, dict] = {}
    code_examples: dict[str, list] = {}

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        routes = {
            "/api/style-guide": self._handle_style_guide,
            "/api/migration-guide": self._handle_migration_guide,
            "/api/search": self._handle_search,
            "/api/examples": self._handle_examples,
            "/health": self._handle_health,
        }

        handler = routes.get(path)
        if handler:
            handler(params)
        elif path.startswith("/api/context/"):
            self._handle_context(path, params)
        else:
            self._send_error(404, "Not found")

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/validate":
            self._handle_validate()
        else:
            self._send_error(404, "Not found")

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status: int, message: str) -> None:
        """Send error response."""
        self._send_json({"error": message}, status)

    def _handle_health(self, params: dict) -> None:
        """Handle health check endpoint."""
        self._send_json({"status": "healthy"})

    def _handle_style_guide(self, params: dict) -> None:
        """Handle style guide requests."""
        language = params.get("language", ["python"])[0]
        
        # Default Python style guide
        default_guide = """# Python Style Guide

## General Guidelines
- Follow PEP 8 conventions
- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use type hints for all function signatures

## Naming Conventions
- Classes: PascalCase
- Functions and variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private attributes: _leading_underscore

## Documentation
- Use docstrings for all public modules, functions, classes, and methods
- Follow Google-style docstring format
- Include type information in docstrings

## Imports
- Group imports: standard library, third-party, local
- Sort imports alphabetically within groups
- Use absolute imports

## Error Handling
- Use specific exception types
- Always include error messages
- Log errors appropriately
"""
        
        content = self.style_guides.get(language, default_guide)
        self._send_json({"content": content})

    def _handle_migration_guide(self, params: dict) -> None:
        """Handle migration guide requests."""
        source = params.get("source", [""])[0]
        target = params.get("target", [""])[0]
        
        key = f"{source}_to_{target}"
        
        default_guides = {
            "python2_to_python3": {
                "title": "Python 2 to Python 3 Migration Guide",
                "sections": [
                    {
                        "name": "Print Function",
                        "description": "Replace print statements with print() function",
                        "example": "print 'hello' -> print('hello')"
                    },
                    {
                        "name": "Division",
                        "description": "True division is default in Python 3",
                        "example": "5 / 2 returns 2.5 in Python 3"
                    },
                    {
                        "name": "Unicode",
                        "description": "All strings are unicode by default",
                        "example": "str -> str (unicode), bytes for binary"
                    }
                ]
            },
            "flask_to_fastapi": {
                "title": "Flask to FastAPI Migration Guide",
                "sections": [
                    {
                        "name": "Route Decorators",
                        "description": "Replace @app.route() with specific method decorators",
                        "example": "@app.route('/') -> @app.get('/')"
                    },
                    {
                        "name": "Request Data",
                        "description": "Use dependency injection instead of global request",
                        "example": "request.json -> async def endpoint(data: Model)"
                    },
                    {
                        "name": "Response",
                        "description": "Return dicts or Pydantic models directly",
                        "example": "jsonify(data) -> return data"
                    }
                ]
            }
        }
        
        guide = self.migration_guides.get(key, default_guides.get(key, {}))
        self._send_json(guide)

    def _handle_search(self, params: dict) -> None:
        """Handle documentation search requests."""
        query = params.get("q", [""])[0].lower()
        limit = int(params.get("limit", ["5"])[0])
        
        # Simple mock search results
        results = []
        
        if "python" in query or "py3" in query:
            results.append({
                "title": "Python 3 Migration Best Practices",
                "url": "/docs/python3-migration",
                "snippet": "Guide for migrating Python 2 code to Python 3..."
            })
        
        if "flask" in query or "fastapi" in query:
            results.append({
                "title": "FastAPI Migration Guide",
                "url": "/docs/fastapi-migration",
                "snippet": "How to migrate Flask applications to FastAPI..."
            })
        
        if "style" in query or "guide" in query:
            results.append({
                "title": "Company Style Guide",
                "url": "/docs/style-guide",
                "snippet": "Official coding style guidelines..."
            })
        
        self._send_json({"results": results[:limit]})

    def _handle_examples(self, params: dict) -> None:
        """Handle code example requests."""
        pattern = params.get("pattern", [""])[0]
        target = params.get("target", [""])[0]
        
        # Default examples
        default_examples = {
            "flask_route": [
                {
                    "before": "@app.route('/users', methods=['GET'])\ndef get_users():\n    return jsonify(users)",
                    "after": "@app.get('/users')\nasync def get_users():\n    return users"
                }
            ],
            "print_statement": [
                {
                    "before": "print 'Hello, World!'",
                    "after": "print('Hello, World!')"
                }
            ]
        }
        
        examples = self.code_examples.get(pattern, default_examples.get(pattern, []))
        self._send_json({"examples": examples})

    def _handle_context(self, path: str, params: dict) -> None:
        """Handle generic context requests."""
        context_type = path.replace("/api/context/", "")
        
        contexts = {
            "testing": "Use pytest for testing. Write unit tests for all public functions.",
            "security": "Never commit secrets. Use environment variables for configuration.",
            "performance": "Use generators for large data. Profile before optimizing.",
        }
        
        content = contexts.get(context_type, "")
        self._send_json({"content": content})

    def _handle_validate(self) -> None:
        """Handle code validation requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            code = data.get("code", "")
            language = data.get("language", "python")
            
            # Simple validation (in production, use actual linters)
            issues = []
            
            if language == "python":
                lines = code.split("\n")
                for i, line in enumerate(lines, 1):
                    if len(line) > 100:
                        issues.append({
                            "line": i,
                            "message": f"Line exceeds 100 characters ({len(line)})"
                        })
                    if "\t" in line:
                        issues.append({
                            "line": i,
                            "message": "Use spaces instead of tabs"
                        })
            
            self._send_json({
                "valid": len(issues) == 0,
                "issues": issues
            })
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


class MCPServer:
    """
    Local MCP server for DevAssist.
    
    Provides documentation context to migration agents including:
    - Style guides
    - Migration patterns
    - Code examples
    - Validation services
    """

    def __init__(self, host: str = "localhost", port: int = 3000) -> None:
        self.host = host
        self.port = port
        self.server: HTTPServer | None = None

    def load_style_guide(self, language: str, content: str) -> None:
        """Load a style guide into the server."""
        MCPRequestHandler.style_guides[language] = content

    def load_style_guide_from_file(self, language: str, file_path: Path) -> None:
        """Load a style guide from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            self.load_style_guide(language, f.read())

    def load_migration_guide(
        self, source: str, target: str, guide: dict
    ) -> None:
        """Load a migration guide into the server."""
        key = f"{source}_to_{target}"
        MCPRequestHandler.migration_guides[key] = guide

    def load_code_examples(self, pattern: str, examples: list) -> None:
        """Load code examples for a pattern."""
        MCPRequestHandler.code_examples[pattern] = examples

    def start(self) -> None:
        """Start the MCP server."""
        self.server = HTTPServer((self.host, self.port), MCPRequestHandler)
        print(f"MCP Server running on http://{self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self) -> None:
        """Stop the MCP server."""
        if self.server:
            self.server.shutdown()
            self.server = None

    def __enter__(self) -> "MCPServer":
        """Context manager entry."""
        import threading
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
