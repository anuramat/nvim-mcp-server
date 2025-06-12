"""Tests for MCP tools."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from nvim_mcp_server.core import NeovimMCPServer
from mcp.types import TextContent


class TestMCPTools:
    """Test MCP tool implementations."""

    @pytest.fixture
    def mock_nvim(self):
        """Create a mock Neovim instance."""
        nvim = Mock()
        nvim.current.buffer = Mock()
        nvim.current.buffer.number = 1
        nvim.current.buffer.__getitem__ = Mock(
            return_value=["line 1", "line 2", "line 3"]
        )
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

    @pytest.fixture
    def server(self, mock_nvim):
        """Create MCP server with mock Neovim."""
        return NeovimMCPServer(mock_nvim)

    @pytest.mark.asyncio
    async def test_get_buffer_content(self, server, mock_nvim):
        """Test getting buffer content."""
        result = await server._get_buffer_content()

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "line 1\nline 2\nline 3"

    @pytest.mark.asyncio
    async def test_get_buffer_content_with_id(self, server, mock_nvim):
        """Test getting specific buffer content."""
        buffer2 = Mock()
        buffer2.__getitem__ = Mock(return_value=["buffer 2 content"])
        mock_nvim.buffers = {2: buffer2}

        result = await server._get_buffer_content(buffer_id=2)

        assert len(result) == 1
        assert result[0].text == "buffer 2 content"

    @pytest.mark.asyncio
    async def test_edit_buffer(self, server, mock_nvim):
        """Test editing buffer content."""
        mock_buffer = Mock()
        mock_buffer.__setitem__ = Mock()
        mock_nvim.current.buffer = mock_buffer

        result = await server._edit_buffer("new content\nline 2")

        # Check that buffer was updated
        mock_buffer.__setitem__.assert_called_with(
            slice(None, None, None), ["new content", "line 2"]
        )
        assert len(result) == 1
        assert result[0].text == "Buffer updated successfully"

    @pytest.mark.asyncio
    async def test_edit_buffer_partial(self, server, mock_nvim):
        """Test editing partial buffer content."""
        mock_buffer = Mock()
        mock_buffer.__setitem__ = Mock()
        mock_nvim.current.buffer = mock_buffer

        result = await server._edit_buffer("replacement", line_start=2, line_end=3)

        # Check that specific lines were updated (converted to 0-indexed)
        mock_buffer.__setitem__.assert_called_with(slice(1, 3, None), ["replacement"])
        assert result[0].text == "Buffer updated successfully"

    @pytest.mark.asyncio
    async def test_run_command(self, server, mock_nvim):
        """Test running Vim command."""
        mock_nvim.command_output.return_value = "command result"

        result = await server._run_command("echo 'test'")

        mock_nvim.command_output.assert_called_with("echo 'test'")
        assert len(result) == 1
        assert result[0].text == "command result"

    @pytest.mark.asyncio
    async def test_run_command_no_output(self, server, mock_nvim):
        """Test running command with no output."""
        mock_nvim.command_output.return_value = ""

        result = await server._run_command("set number")

        assert result[0].text == "Command executed successfully"

    @pytest.mark.asyncio
    async def test_get_status(self, server, mock_nvim):
        """Test getting Neovim status."""
        result = await server._get_status()

        assert len(result) == 1
        status_text = result[0].text
        assert "mode:" in status_text
        assert "current_buffer:" in status_text
        assert "buffer_count:" in status_text
        assert "window_count:" in status_text
        assert "cursor_position:" in status_text
        assert "working_directory:" in status_text

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, server, mock_nvim):
        """Test error handling in tools."""
        mock_nvim.current.buffer.__getitem__.side_effect = Exception("Buffer error")

        result = await server._get_buffer_content()

        assert len(result) == 1
        assert "Error getting buffer content" in result[0].text
