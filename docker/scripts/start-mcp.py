#!/usr/bin/env python3
"""Startup script for MCP server."""

import sys
sys.path.insert(0, '/app')

from mcp.server import MCPServer

if __name__ == "__main__":
    import os
    port = int(os.environ.get("MCP_PORT", 3000))
    server = MCPServer(host="0.0.0.0", port=port)
    print(f"Starting MCP server on port {port}")
    server.start()
