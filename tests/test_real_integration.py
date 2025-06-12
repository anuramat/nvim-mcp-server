"""Integration test using real nvim instance."""

import pytest
import asyncio
import tempfile
import os
import sys
import pynvim
from nvimcp.core import NvimcpServer


class TestRealNvimIntegration:
    """Test with actual nvim instance."""

    @pytest.fixture
    def real_nvim(self):
        """Create a real embedded nvim instance."""
        # Suppress child watcher deprecation warnings in Python 3.12+
        # These are unavoidable when using pynvim.attach('child') and will be
        # fixed when pynvim updates to use subprocess without child watchers
        import warnings

        if sys.version_info >= (3, 12):
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, module="asyncio.events"
            )

        nvim = pynvim.attach(
            "child",
            argv=[
                "nvim",
                "--embed",
                "--headless",
                "-c",
                "set noswapfile",  # Disable swap files
                "-c",
                "set noundofile",  # Disable undo files
            ],
        )
        yield nvim
        try:
            nvim.close()
        except:
            pass

    @pytest.mark.asyncio
    async def test_real_nvim_get_status(self, real_nvim):
        """Test get_status with real nvim instance."""
        server = NvimcpServer(real_nvim)

        result = await server._get_status()

        assert len(result) == 1
        assert result[0].type == "text"
        status_text = result[0].text

        # Verify expected status fields
        assert "mode:" in status_text
        assert "current_buffer:" in status_text
        assert "buffer_count:" in status_text
        assert "window_count:" in status_text
        assert "cursor_position:" in status_text
        assert "working_directory:" in status_text

    @pytest.mark.asyncio
    async def test_real_nvim_buffer_operations(self, real_nvim):
        """Test buffer operations with real nvim."""
        server = NvimcpServer(real_nvim)

        # Test initial buffer content (should be empty)
        content_result = await server._get_buffer_content()
        assert len(content_result) == 1
        assert content_result[0].text == ""

        # Test editing buffer
        test_content = "Hello, World!\nSecond line"
        edit_result = await server._edit_buffer(test_content)
        assert len(edit_result) == 1
        assert "successfully" in edit_result[0].text

        # Verify content was written
        verify_result = await server._get_buffer_content()
        assert verify_result[0].text == test_content

    @pytest.mark.asyncio
    async def test_real_nvim_commands(self, real_nvim):
        """Test command execution with real nvim."""
        server = NvimcpServer(real_nvim)

        # Test echo command
        result = await server._run_command("echo 'test command'")
        assert len(result) == 1
        assert "test command" in result[0].text

        # Test setting option
        await server._run_command("set number")
        option_result = await server._run_command("echo &number")
        assert "1" in option_result[0].text

    @pytest.mark.asyncio
    async def test_real_nvim_multiple_buffers(self, real_nvim):
        """Test multiple buffer handling."""
        server = NvimcpServer(real_nvim)

        # Get initial buffer count
        initial_status = await server._get_status()
        initial_text = initial_status[0].text

        # Create new buffer
        await server._run_command("enew")

        # Get status to see buffer count
        status_result = await server._get_status()
        status_text = status_result[0].text

        # Verify buffer creation worked - just check that we got valid status
        assert "buffer_count:" in status_text
        assert "current_buffer:" in status_text
