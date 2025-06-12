#!/usr/bin/env python3
"""Debug script to isolate TaskGroup error."""

import asyncio
import sys
import logging
from nvim_mcp_server.connection import connect_neovim
from nvim_mcp_server.core import NeovimMCPServer

logging.basicConfig(level=logging.DEBUG)


async def test_stdio_minimal():
    """Test minimal stdio server to isolate TaskGroup error."""
    try:
        # Connect to Neovim
        nvim = connect_neovim("socket", "/tmp/nvim.sock")
        print("✓ Connected to Neovim", file=sys.stderr)

        # Create server
        server = NeovimMCPServer(nvim)
        print("✓ Created MCP server", file=sys.stderr)

        # Test individual components
        from mcp.server.stdio import stdio_server

        print("Testing stdio_server creation...", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print("✓ stdio_server context created", file=sys.stderr)

            # Create initialization options
            init_options = server.server.create_initialization_options()
            print("✓ Created init options", file=sys.stderr)

            # Try to start the server with a timeout
            print("Starting server.run()...", file=sys.stderr)

            # This is where the TaskGroup error likely occurs
            await asyncio.wait_for(
                server.server.run(read_stream, write_stream, init_options), timeout=1.0
            )

    except asyncio.TimeoutError:
        print("✓ Timeout as expected (no client input)", file=sys.stderr)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(test_stdio_minimal())
