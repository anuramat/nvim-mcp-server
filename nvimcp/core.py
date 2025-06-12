"""Core nvimcp server implementation."""

import asyncio
import logging
from typing import Any, Dict, List
import pynvim
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


class NvimcpServer:
    """Nvimcp server that exposes nvim functionality."""

    def __init__(self, nvim: pynvim.Nvim):
        self.nvim = nvim
        self.server = Server("nvimcp", version="0.1.0")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up nvimcp server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_buffer_content",
                    description="Get content of current or specified buffer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "buffer_id": {
                                "type": "integer",
                                "description": "Buffer ID (optional, defaults to current)",
                            }
                        },
                    },
                ),
                Tool(
                    name="edit_buffer",
                    description="Edit buffer content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "New content for the buffer",
                            },
                            "buffer_id": {
                                "type": "integer",
                                "description": "Buffer ID (optional, defaults to current)",
                            },
                            "line_start": {
                                "type": "integer",
                                "description": "Start line (1-indexed, optional)",
                            },
                            "line_end": {
                                "type": "integer",
                                "description": "End line (1-indexed, optional)",
                            },
                        },
                        "required": ["content"],
                    },
                ),
                Tool(
                    name="run_command",
                    description="Execute Vim command",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Vim command to execute",
                            }
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="get_status",
                    description="Get nvim status information",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_buffer_content":
                    return await self._get_buffer_content(**arguments)
                elif name == "edit_buffer":
                    return await self._edit_buffer(**arguments)
                elif name == "run_command":
                    return await self._run_command(**arguments)
                elif name == "get_status":
                    return await self._get_status(**arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Tool {name} failed: {e}")
                return [TextContent(type="text", text=f"Error: {e}")]

    async def _get_buffer_content(self, buffer_id: int = None) -> List[TextContent]:
        """Get buffer content."""
        try:
            # Run in thread to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._sync_get_buffer_content, buffer_id
            )
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting buffer content: {e}")]

    def _sync_get_buffer_content(self, buffer_id: int = None) -> str:
        """Synchronous buffer content retrieval."""
        if buffer_id is None:
            buffer = self.nvim.current.buffer
        else:
            buffer = self.nvim.buffers[buffer_id]
        return "\n".join(buffer[:])

    async def _edit_buffer(
        self,
        content: str,
        buffer_id: int = None,
        line_start: int = None,
        line_end: int = None,
    ) -> List[TextContent]:
        """Edit buffer content."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._sync_edit_buffer, content, buffer_id, line_start, line_end
            )
            return [TextContent(type="text", text="Buffer updated successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error editing buffer: {e}")]

    def _sync_edit_buffer(
        self,
        content: str,
        buffer_id: int = None,
        line_start: int = None,
        line_end: int = None,
    ):
        """Synchronous buffer editing."""
        if buffer_id is None:
            buffer = self.nvim.current.buffer
        else:
            buffer = self.nvim.buffers[buffer_id]

        lines = content.split("\n")

        if line_start is not None and line_end is not None:
            buffer[line_start - 1 : line_end] = lines
        elif line_start is not None:
            buffer[line_start - 1 :] = lines
        else:
            buffer[:] = lines

    async def _run_command(self, command: str) -> List[TextContent]:
        """Execute Vim command."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._sync_run_command, command)
            return [
                TextContent(type="text", text=result or "Command executed successfully")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Command failed: {e}")]

    def _sync_run_command(self, command: str) -> str:
        """Synchronous command execution."""
        return self.nvim.command_output(command)

    async def _get_status(self) -> List[TextContent]:
        """Get Neovim status."""
        try:
            # Run in thread executor to avoid event loop conflicts
            import concurrent.futures
            import threading

            # Use a separate thread pool for Neovim operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._sync_get_status)
                status = future.result(timeout=5.0)

            return [TextContent(type="text", text=status)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting status: {e}")]

    def _sync_get_status(self) -> str:
        """Synchronous status retrieval."""
        try:
            # Use direct request calls instead of convenience properties
            info = {
                "mode": self.nvim.request("nvim_get_mode"),
                "current_buffer": self.nvim.request("nvim_get_current_buf"),
                "buffer_count": len(self.nvim.request("nvim_list_bufs")),
                "window_count": len(self.nvim.request("nvim_list_wins")),
                "cursor_position": self.nvim.request("nvim_win_get_cursor", 0),
                "working_directory": self.nvim.request("nvim_eval", "getcwd()"),
            }
            return "\n".join(f"{k}: {v}" for k, v in info.items())
        except Exception as e:
            return f"Error getting status: {e}"

    async def run(self):
        """Run the MCP server via stdio."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )
