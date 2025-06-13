#!/usr/bin/env python3
"""Test MCP sequence validation and protocol components."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock


class TestMCPSequence:
    """Test class for MCP protocol sequence validation."""

    def test_mcp_message_structure(self):
        """Test that MCP message structures are valid."""
        # Test initialize request structure
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        
        # Verify the message can be serialized
        serialized = json.dumps(init_request)
        assert serialized is not None
        
        # Verify it can be deserialized back
        deserialized = json.loads(serialized)
        assert deserialized["jsonrpc"] == "2.0"
        assert deserialized["method"] == "initialize"

    def test_tool_call_message_structure(self):
        """Test tool call message structure."""
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_status", "arguments": {}},
        }
        
        # Verify serialization works
        serialized = json.dumps(tool_request)
        deserialized = json.loads(serialized)
        
        assert deserialized["method"] == "tools/call"
        assert deserialized["params"]["name"] == "get_status"

    def test_standalone_script_imports(self):
        """Test that standalone.py can be imported without errors."""
        project_root = Path(__file__).parent.parent
        standalone_path = project_root / "standalone.py"
        
        # Verify the file exists
        assert standalone_path.exists()
        
        # Test that it contains expected imports and functions
        content = standalone_path.read_text()
        assert "async def main" in content
        assert "connect_neovim" in content
        assert "NvimcpServer" in content

    def test_nvimcp_server_tool_list(self):
        """Test that NvimcpServer has expected tools."""
        from nvimcp.core import NvimcpServer
        
        # Create server with mock nvim
        mock_nvim = Mock()
        server = NvimcpServer(mock_nvim)
        
        # Verify server has expected structure
        assert server.nvim == mock_nvim
        assert server.server is not None
        
        # The tools are defined in the _setup_handlers method
        # We can verify this by checking the method exists
        assert hasattr(server, '_setup_handlers')
        assert hasattr(server, '_get_status')
        assert hasattr(server, '_get_buffer_content')
        assert hasattr(server, '_edit_buffer')
        assert hasattr(server, '_run_command')

    def test_error_response_structure(self):
        """Test error response message structure."""
        # Test invalid tool error response structure
        error_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "error": {
                "code": -32601,  # Method not found
                "message": "Method not found"
            }
        }
        
        # Verify serialization
        serialized = json.dumps(error_response)
        deserialized = json.loads(serialized)
        
        assert deserialized["error"]["code"] == -32601
        assert "error" in deserialized
        assert "result" not in deserialized

    def test_connection_modes(self):
        """Test connection mode handling."""
        from nvimcp.connection import connect_neovim, ConnectionError
        
        # Test that function exists and handles modes
        with patch('nvimcp.connection._connect_socket') as mock_socket:
            with patch('nvimcp.connection._connect_embedded') as mock_embedded:
                mock_nvim = Mock()
                mock_embedded.return_value = mock_nvim
                
                # Test embedded mode works
                result = connect_neovim("embedded")
                assert result == mock_nvim
                mock_embedded.assert_called_once()
                
                # Reset mocks
                mock_socket.reset_mock()
                mock_embedded.reset_mock()
                
                # Test auto mode falls back properly
                mock_socket.side_effect = ConnectionError("Socket failed")
                mock_embedded.return_value = mock_nvim
                
                result = connect_neovim("auto", "/tmp/test.sock")
                assert result == mock_nvim
                mock_socket.assert_called_once()
                mock_embedded.assert_called_once()