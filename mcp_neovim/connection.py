"""Neovim connection management for MCP server."""

import logging
import asyncio
from typing import Optional
import pynvim

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Raised when connection to Neovim fails."""

    pass


def connect_neovim(
    mode: str = "auto",
    socket_path: str = "/tmp/nvim.sock",
    nvim_args: Optional[list] = None,
) -> pynvim.Nvim:
    """
    Connect to Neovim instance.

    Args:
        mode: Connection mode - "auto", "socket", or "embedded"
        socket_path: Path to Neovim socket (for socket mode)
        nvim_args: Additional arguments for embedded mode

    Returns:
        Connected Neovim instance

    Raises:
        ConnectionError: If connection fails
    """
    if nvim_args is None:
        nvim_args = ["nvim", "--embed", "--headless"]

    if mode == "auto":
        # Try socket first, fallback to embedded
        try:
            return _connect_socket(socket_path)
        except Exception as e:
            logger.info(f"Socket connection failed ({e}), trying embedded mode")
            return _connect_embedded(nvim_args)

    elif mode == "socket":
        return _connect_socket(socket_path)

    elif mode == "embedded":
        return _connect_embedded(nvim_args)

    else:
        raise ConnectionError(f"Invalid connection mode: {mode}")


def _connect_socket(socket_path: str) -> pynvim.Nvim:
    """Connect to existing Neovim instance via socket."""
    try:
        # Use synchronous connection to avoid event loop conflicts
        import socket
        import os

        # Check if socket exists
        if not os.path.exists(socket_path):
            raise ConnectionError(f"Socket path does not exist: {socket_path}")

        # Test socket connectivity
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(socket_path)
            sock.close()
        except Exception as e:
            raise ConnectionError(f"Cannot connect to socket: {e}")

        # Force synchronous mode by not running in async context
        import threading

        nvim_result = [None]
        error_result = [None]

        def connect_sync():
            try:
                nvim = pynvim.attach("socket", path=socket_path)
                nvim.command('echo "MCP server connected"')
                nvim_result[0] = nvim
            except Exception as e:
                error_result[0] = e

        thread = threading.Thread(target=connect_sync)
        thread.start()
        thread.join()

        if error_result[0]:
            raise error_result[0]
        if not nvim_result[0]:
            raise ConnectionError("Failed to connect - unknown error")

        logger.info(f"Connected to Neovim via socket: {socket_path}")
        return nvim_result[0]
    except Exception as e:
        raise ConnectionError(f"Failed to connect via socket {socket_path}: {e}")


def _connect_embedded(nvim_args: list) -> pynvim.Nvim:
    """Start embedded Neovim instance."""
    try:
        import threading

        nvim_result = [None]
        error_result = [None]

        def connect_sync():
            try:
                nvim = pynvim.attach("child", argv=nvim_args)
                nvim.command('echo "MCP server connected (embedded)"')
                nvim_result[0] = nvim
            except Exception as e:
                error_result[0] = e

        thread = threading.Thread(target=connect_sync)
        thread.start()
        thread.join()

        if error_result[0]:
            raise error_result[0]
        if not nvim_result[0]:
            raise ConnectionError("Failed to connect - unknown error")

        logger.info(f"Started embedded Neovim: {' '.join(nvim_args)}")
        return nvim_result[0]
    except Exception as e:
        raise ConnectionError(f"Failed to start embedded Neovim: {e}")
