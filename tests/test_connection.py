"""Tests for connection management."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from nvimcp.connection import (
    connect_neovim,
    ConnectionError,
    _connect_embedded,
)


class TestConnectionManagement:
    """Test nvim connection functionality."""

    def test_invalid_mode_raises_error(self):
        """Test that invalid connection mode raises error."""
        with pytest.raises(ConnectionError, match="Invalid connection mode"):
            connect_neovim(mode="invalid")

    def test_socket_path_not_exists(self):
        """Test socket mode with non-existent socket path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            socket_path = os.path.join(tmpdir, "nonexistent.sock")
            with pytest.raises(ConnectionError, match="Socket path does not exist"):
                connect_neovim(mode="socket", socket_path=socket_path)

    @patch("nvimcp.connection.pynvim.attach")
    @patch("socket.socket")
    @patch("os.path.exists")
    def test_socket_connection_success(self, mock_exists, mock_socket, mock_attach):
        """Test successful socket connection."""
        # Setup mocks
        mock_exists.return_value = True
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        mock_nvim = Mock()
        mock_attach.return_value = mock_nvim

        # Test connection
        result = connect_neovim(mode="socket", socket_path="/tmp/test.sock")

        # Verify calls
        mock_exists.assert_called_with("/tmp/test.sock")
        mock_sock.connect.assert_called_with("/tmp/test.sock")
        mock_sock.close.assert_called_once()
        mock_nvim.command.assert_called_with('echo "nvimcp server connected"')
        assert result == mock_nvim

    @patch("nvimcp.connection.pynvim.attach")
    def test_embedded_connection_success(self, mock_attach):
        """Test successful embedded connection."""
        mock_nvim = Mock()
        mock_attach.return_value = mock_nvim

        result = connect_neovim(mode="embedded")

        mock_nvim.command.assert_called_with('echo "nvimcp server connected (embedded)"')
        assert result == mock_nvim

    @patch("nvimcp.connection._connect_socket")
    @patch("nvimcp.connection._connect_embedded")
    def test_auto_mode_fallback(self, mock_embedded, mock_socket):
        """Test auto mode falls back to embedded when socket fails."""
        mock_socket.side_effect = ConnectionError("Socket failed")
        mock_nvim = Mock()
        mock_embedded.return_value = mock_nvim

        result = connect_neovim(mode="auto")

        mock_socket.assert_called_once()
        mock_embedded.assert_called_once()
        assert result == mock_nvim
