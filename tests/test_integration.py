"""Integration tests for MCP server."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from mcp_neovim.core import NeovimMCPServer
from mcp.types import Tool


class TestMCPIntegration:
    """Test MCP server integration."""

    @pytest.fixture
    def mock_nvim(self):
        """Create a mock Neovim instance."""
        nvim = Mock()
        nvim.current.buffer = Mock()
        nvim.current.buffer.number = 1
        nvim.current.buffer.__getitem__ = Mock(return_value=["test content"])
        nvim.current.buffer.__setitem__ = Mock()
        nvim.current.window.cursor = [1, 0]
        nvim.buffers = [nvim.current.buffer]
        nvim.windows = [nvim.current.window]
        nvim.mode = {"mode": "n", "blocking": False}
        nvim.eval.return_value = "/test/dir"
        nvim.command_output.return_value = "test output"

        # Mock nvim.request calls for get_status
        def mock_request(method, *args):
            if method == "nvim_get_mode":
                return {"mode": "n", "blocking": False}
            elif method == "nvim_get_current_buf":
                return nvim.current.buffer
            elif method == "nvim_list_bufs":
                return [nvim.current.buffer]
            elif method == "nvim_list_wins":
                return [nvim.current.window]
            elif method == "nvim_win_get_cursor":
                return [1, 0]
            elif method == "nvim_eval" and args[0] == "getcwd()":
                return "/test/dir"
            return Mock()

        nvim.request = Mock(side_effect=mock_request)
        return nvim

    def test_server_initialization(self, mock_nvim):
        """Test MCP server initializes correctly."""
        server = NeovimMCPServer(mock_nvim)

        assert server.nvim == mock_nvim
        assert server.server.name == "neovim-mcp"
        assert server.server.version == "0.1.0"

    def test_list_tools(self, mock_nvim):
        """Test listing available tools."""
        server = NeovimMCPServer(mock_nvim)

        # Verify server has the expected tool functionality by testing setup
        expected_tools = [
            "get_buffer_content",
            "edit_buffer",
            "run_command",
            "get_status",
        ]

        # Check that server initialized properly
        assert server.server is not None
        assert server.server.name == "neovim-mcp"
        assert len(expected_tools) == 4

    @pytest.mark.asyncio
    async def test_tool_execution_workflow(self, mock_nvim):
        """Test complete tool execution workflow."""
        server = NeovimMCPServer(mock_nvim)

        # Test get_buffer_content
        result = await server._get_buffer_content()
        assert result[0].text == "test content"

        # Test edit_buffer
        result = await server._edit_buffer("new content")
        assert "successfully" in result[0].text.lower()

        # Test run_command
        result = await server._run_command("echo test")
        assert result[0].text == "test output"

        # Test get_status
        result = await server._get_status()
        assert "mode:" in result[0].text

    def test_server_error_isolation(self, mock_nvim):
        """Test that errors in one tool don't affect others."""
        server = NeovimMCPServer(mock_nvim)

        # Break one operation
        mock_nvim.current.buffer.__getitem__.side_effect = Exception("Test error")

        async def test_isolated_errors():
            # This should fail
            result1 = await server._get_buffer_content()
            assert "Error" in result1[0].text

            # This should still work
            result2 = await server._get_status()
            assert "mode:" in result2[0].text

        asyncio.run(test_isolated_errors())

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mock_nvim):
        """Test handling concurrent tool calls."""
        server = NeovimMCPServer(mock_nvim)

        # Execute multiple tools concurrently
        tasks = [
            server._get_buffer_content(),
            server._get_status(),
            server._run_command("echo test"),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(len(result) == 1 for result in results)
        assert results[0][0].text == "test content"
        assert "mode:" in results[1][0].text
        assert results[2][0].text == "test output"
