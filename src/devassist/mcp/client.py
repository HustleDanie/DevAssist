"""
MCP Client - Client for connecting to MCP documentation servers.

This client connects to MCP servers to retrieve context from
internal documentation, style guides, and other knowledge bases.
"""

import httpx
from typing import Any

from devassist.core.config import get_settings


class MCPClient:
    """
    Client for MCP (Model Context Protocol) servers.
    
    Connects to documentation servers to retrieve:
    - Style guide information
    - API documentation
    - Internal coding standards
    - Migration-specific guidance
    """

    def __init__(self, server_url: str | None = None) -> None:
        settings = get_settings()
        self.server_url = server_url or settings.mcp_server_url
        self.enabled = settings.mcp_enabled
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(base_url=self.server_url, timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.server_url, timeout=30.0)
        return self._client

    async def get_style_guide(self, language: str = "python") -> str:
        """
        Get the style guide for a specific language.
        
        Args:
            language: Programming language (default: python)
            
        Returns:
            Style guide content as string
        """
        if not self.enabled:
            return ""
        
        try:
            response = await self.client.get(
                "/api/style-guide",
                params={"language": language}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("content", "")
        except Exception:
            return ""

    async def get_migration_guide(
        self, source: str, target: str
    ) -> dict[str, Any]:
        """
        Get migration guide for a specific migration type.
        
        Args:
            source: Source framework/version (e.g., "python2", "flask")
            target: Target framework/version (e.g., "python3", "fastapi")
            
        Returns:
            Dictionary with migration guidance
        """
        if not self.enabled:
            return {}
        
        try:
            response = await self.client.get(
                "/api/migration-guide",
                params={"source": source, "target": target}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

    async def search_documentation(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search internal documentation.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documentation entries
        """
        if not self.enabled:
            return []
        
        try:
            response = await self.client.get(
                "/api/search",
                params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception:
            return []

    async def get_code_examples(
        self, pattern_type: str, target_version: str
    ) -> list[dict[str, str]]:
        """
        Get code examples for a specific pattern migration.
        
        Args:
            pattern_type: Type of pattern (e.g., "flask_route")
            target_version: Target framework/version
            
        Returns:
            List of code examples with before/after
        """
        if not self.enabled:
            return []
        
        try:
            response = await self.client.get(
                "/api/examples",
                params={"pattern": pattern_type, "target": target_version}
            )
            response.raise_for_status()
            return response.json().get("examples", [])
        except Exception:
            return []

    async def validate_code(
        self, code: str, language: str = "python"
    ) -> dict[str, Any]:
        """
        Validate code against style guide rules.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            Validation results with any issues found
        """
        if not self.enabled:
            return {"valid": True, "issues": []}
        
        try:
            response = await self.client.post(
                "/api/validate",
                json={"code": code, "language": language}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"valid": True, "issues": []}

    async def get_context(
        self, context_type: str, **kwargs
    ) -> str:
        """
        Get arbitrary context from MCP server.
        
        Args:
            context_type: Type of context to retrieve
            **kwargs: Additional parameters
            
        Returns:
            Context content as string
        """
        if not self.enabled:
            return ""
        
        try:
            response = await self.client.get(
                f"/api/context/{context_type}",
                params=kwargs
            )
            response.raise_for_status()
            return response.json().get("content", "")
        except Exception:
            return ""

    def sync_get_style_guide(self, language: str = "python") -> str:
        """
        Synchronous version of get_style_guide.
        
        Args:
            language: Programming language
            
        Returns:
            Style guide content
        """
        if not self.enabled:
            return ""
        
        try:
            with httpx.Client(base_url=self.server_url, timeout=30.0) as client:
                response = client.get(
                    "/api/style-guide",
                    params={"language": language}
                )
                response.raise_for_status()
                return response.json().get("content", "")
        except Exception:
            return ""
