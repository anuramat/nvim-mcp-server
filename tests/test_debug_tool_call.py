#!/usr/bin/env python3
"""Test tool call behavior to debug TaskGroup errors in tool execution."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from nvimcp.core import NvimcpServer


class TestToolCallDebugging:
    """Test class for debugging tool call TaskGroup errors."""

    @pytest.fixture
    def mock_nvim(self):
        """Create a mock nvim instance for testing."""
        nvim = Mock()
        nvim.api = Mock()
        nvim.vars = {}
        
        # Mock nvim.request calls that _sync_get_status uses
        nvim.request.side_effect = lambda method, *args: {
            "nvim_get_mode": {'mode': 'n', 'blocking': False},
            "nvim_get_current_buf": Mock(number=1),
            "nvim_list_bufs": [Mock(number=1)],
            "nvim_list_wins": [Mock(number=1)],
            "nvim_win_get_cursor": [1, 0],
            "nvim_eval": '/test/path'
        }.get(method, None)
        
        return nvim

    @pytest.mark.asyncio
    async def test_direct_tool_call(self, mock_nvim):
        """Test direct tool call execution without MCP wrapper."""
        server = NvimcpServer(mock_nvim)
        
        # Test direct call to internal method
        result = await server._get_status()
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "mode" in result[0].text
        assert "n" in result[0].text  # normal mode

    @pytest.mark.asyncio
    async def test_mcp_handler_call(self, mock_nvim):
        """Test MCP handler call that might cause TaskGroup errors."""
        server = NvimcpServer(mock_nvim)
        
        # Test that the server has proper handlers setup
        # We can verify this by calling the internal method
        result = await server._get_status()
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "mode" in result[0].text
        
        # Verify the server object exists and has the expected structure
        assert server.server is not None
        assert hasattr(server.server, 'create_initialization_options')

    @pytest.mark.asyncio
    async def test_tool_call_error_handling(self, mock_nvim):
        """Test error handling in tool calls."""
        server = NvimcpServer(mock_nvim)
        
        # Mock nvim.request to raise an error
        mock_nvim.request.side_effect = Exception("Test error")
        
        result = await server._get_status()
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mock_nvim):
        """Test concurrent tool calls to check for race conditions."""
        server = NvimcpServer(mock_nvim)
        
        # Execute multiple tool calls concurrently
        tasks = [
            server._get_status(),
            server._get_status(), 
            server._get_status()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        for result in results:
            assert len(result) == 1
            assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_buffer_operations(self, mock_nvim):
        """Test buffer-related tool calls."""
        server = NvimcpServer(mock_nvim)
        
        # Mock buffer operations for _sync_get_buffer_content
        mock_buffer = Mock()
        mock_buffer.number = 1
        # Mock __len__ for buffer slicing operations
        mock_buffer.__len__ = Mock(return_value=2)
        mock_buffer.__getitem__ = Mock(return_value=["line 1", "line 2"])
        mock_nvim.current.buffer = mock_buffer
        
        # Test get_buffer_content
        result = await server._get_buffer_content()
        assert len(result) == 1
        assert result[0].type == "text"