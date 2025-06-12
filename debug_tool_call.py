#!/usr/bin/env python3
"""Debug tool call TaskGroup error."""

import asyncio
import sys
import logging
import traceback
from nvimcp.connection import connect_neovim
from nvimcp.core import NvimcpServer

logging.basicConfig(level=logging.DEBUG)


async def test_tool_call_error():
    """Isolate the tool call TaskGroup error."""
    try:
        # Connect to Neovim
        nvim = connect_neovim("socket", "/tmp/nvim.sock")
        print("✓ Connected to nvim", file=sys.stderr)

        # Create server
        server = NvimcpServer(nvim)
        print("✓ Created nvimcp server", file=sys.stderr)

        # Test direct tool call (this should work)
        print("Testing direct tool call...", file=sys.stderr)
        result = await server._get_status()
        print(f"✓ Direct call works: {result[0].text[:50]}...", file=sys.stderr)

        # Test MCP handler (this might cause the error)
        print("Testing nvimcp handler...", file=sys.stderr)
        from mcp.types import CallToolRequest

        # Manually call the handler that MCP server would call
        try:
            handler_result = await server.handle_call_tool("get_status", {})
            print(f"✓ Handler works: {handler_result[0].text[:50]}...", file=sys.stderr)
        except Exception as e:
            print(f"✗ Handler error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(test_tool_call_error())
