#!/usr/bin/env python3
"""Test TaskGroup behavior to debug server initialization issues."""

import asyncio
import pytest
import sys
from unittest.mock import Mock, patch
from nvimcp.core import NvimcpServer


class TestTaskGroupDebugging:
    """Test class for debugging TaskGroup-related errors in server initialization."""

    @pytest.fixture
    def mock_nvim(self):
        """Create a mock nvim instance for testing."""
        nvim = Mock()
        nvim.api = Mock()
        nvim.vars = {}
        return nvim

    @pytest.mark.asyncio
    async def test_server_creation(self, mock_nvim):
        """Test that NvimcpServer can be created without errors."""
        server = NvimcpServer(mock_nvim)
        
        # Test that server initialization doesn't raise errors
        assert server is not None
        assert server.nvim == mock_nvim
        
        # Test initialization options creation
        init_options = server.server.create_initialization_options()
        assert init_options is not None

    @pytest.mark.asyncio 
    async def test_tool_execution_isolation(self, mock_nvim):
        """Test tool execution works in isolation."""
        server = NvimcpServer(mock_nvim)
        
        # Mock nvim.request calls that _sync_get_status uses
        mock_nvim.request.side_effect = lambda method, *args: {
            "nvim_get_mode": {'mode': 'n', 'blocking': False},
            "nvim_get_current_buf": Mock(number=1),
            "nvim_list_bufs": [Mock(number=1)],
            "nvim_list_wins": [Mock(number=1)],
            "nvim_win_get_cursor": [1, 0],
            "nvim_eval": '/test/path'
        }.get(method, None)
        
        # Test direct tool call
        result = await server._get_status()
        assert len(result) == 1
        assert result[0].type == "text"
        assert "mode" in result[0].text

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection error handling behavior."""
        from nvimcp.connection import connect_neovim, ConnectionError
        
        # Test that connection errors are properly handled
        with patch('nvimcp.connection._connect_socket') as mock_socket:
            with patch('nvimcp.connection._connect_embedded') as mock_embedded:
                mock_socket.side_effect = ConnectionError("Socket failed")
                mock_embedded.side_effect = ConnectionError("Embedded failed")
                
                with pytest.raises(ConnectionError):
                    connect_neovim("auto", "/tmp/nonexistent.sock")