"""
MCP (Model Context Protocol) integration module.

Provides integration with MCP servers to pull context from
internal documentation wikis and style guides.
"""

from devassist.mcp.client import MCPClient
from devassist.mcp.server import MCPServer

__all__ = ["MCPClient", "MCPServer"]
