# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

# nvimcp - Nvimcp Server

## Development Commands

**Testing:**

- `pytest` - Run all tests with async support
- `pytest tests/test_connection.py` - Run connection tests only
- `pytest tests/test_tools.py` - Run tool tests only
- `pytest tests/test_integration.py` - Run integration tests only
- `pytest -v --tb=short` - Verbose output with short tracebacks

**Linting & Formatting:**

- `black .` - Format Python code
- `mypy nvimcp/` - Type checking

**Development Environment:**

- `nix develop` - Enter Nix development shell with all dependencies
- `export PYTHONPATH="$PWD:$PYTHONPATH"` - Set Python path for local development

**Running the Server:**

- `python standalone.py` - Run in standalone mode (embedded nvim)
- `python standalone.py --socket /tmp/nvim.sock` - Connect to socket
- `python standalone.py --mode auto` - Auto-fallback from socket to embedded

## Architecture Overview

Nvimcp server exposing nvim functionality to external clients via Python and
RPC. Currently implements **standalone mode only** - no plugin mode yet.

**Core Components:**

- `nvimcp/core.py` (201 lines) - Main nvimcp server with tool handlers
- `nvimcp/connection.py` (129 lines) - Connection management for
  different modes
- `standalone.py` (72 lines) - Standalone entry point with connection setup

**Connection Modes (Standalone Only):**

- **Embedded**: `pynvim.attach('child')` - Isolated headless nvim instance
- **Socket**: `pynvim.attach('socket')` - Connect to existing nvim session
- **Auto**: Falls back from socket to embedded if socket unavailable

**Nvimcp Tools Currently Implemented (4 total):**

- `get_buffer_content` - Read buffer contents (current or specific buffer ID)
- `edit_buffer` - Modify buffer text (full or partial replacement)
- `run_command` - Execute Vim commands with output capture
- `get_status` - Get nvim status (mode, buffers, windows, cursor, cwd)

**Not Yet Implemented:**

- Plugin mode (`rplugin/` directory missing)
- Additional tools: `get_diagnostics`, `search_project`, `get_lsp_info`,
  `call_plugin`

**Test Coverage:**

- 22 tests across connection, tools, integration, and real Neovim scenarios
- Async support with pytest-asyncio
- Comprehensive mocking for Neovim interactions
- Real Neovim integration tests with actual process spawning
- Error handling and concurrent execution validation
- Python 3.12+ compatibility with proper deprecation warning handling

## Key Implementation Details

The `NvimcpServer` class in `core.py` is connection-agnostic - it accepts any
`pynvim.Nvim` instance, allowing the same codebase to work in both standalone
and plugin modes. Connection setup is handled separately in `connection.py` and
`standalone.py`.

All tools use async handlers and proper error handling with try/catch blocks
that return meaningful error messages to clients. The server uses the
official Python SDK with stdio transport.

## Current Implementation Status

**✅ Working Features:**

- Standalone nvimcp server (fully functional)
- Socket and embedded nvim connection modes with auto-fallback
- 4 working nvimcp tools: get_buffer_content, edit_buffer, run_command, get_status
- Comprehensive test suite (22 tests passing - including real nvim integration
  tests)
- TaskGroup/event loop conflict resolved using ThreadPoolExecutor
- Compatible with external clients (tested)
- Proper protocol implementation with JSON-RPC
- Python 3.12+ compatibility with deprecation warning handling

**🔧 Key Technical Solutions:**

- Event loop conflict fix: Use `concurrent.futures.ThreadPoolExecutor` instead
  of `asyncio.get_event_loop().run_in_executor()` to avoid conflicts between
  server's event loop and pynvim's async operations
- Connection resilience: Auto-fallback from socket to embedded mode
- Thread safety: Isolated thread pools for nvim API calls
- Python 3.12+ compatibility: Proper handling of asyncio child watcher
  deprecation warnings in real nvim integration tests
- Comprehensive testing: Both mock-based unit tests and real nvim integration
  tests for full coverage

## Next Steps

### 1. Plugin Mode Implementation

Convert to a nvim remote plugin to enable seamless integration:

**Required Changes:**

- Create `rplugin/python/nvimcp.py` with `@neovim.plugin` decorator
- Implement plugin-specific initialization using `nvim` instance from plugin
  host
- Add plugin registration commands and autocommands
- Handle plugin lifecycle (start/stop nvimcp server on demand)

**Benefits:**

- No external process management required
- Automatic startup with nvim
- Direct access to nvim's Lua integration
- Shared lifecycle and configuration

### 2. Enhanced Tool Set

Expand nvimcp capabilities with additional tools:

**High Priority:**

- `get_diagnostics` - LSP diagnostics via `vim.diagnostic.get()`
- `search_project` - Project-wide search using `:grep`/`:vimgrep`
- `get_lsp_info` - Language server and completion information
- `get_file_tree` - Project structure navigation

**Advanced Tools:**

- `call_lua_function` - Execute arbitrary Lua code
- `get_git_info` - Git status and branch information
- `manage_sessions` - Session save/restore functionality
- `plugin_management` - Install/configure plugins

### 3. Performance & Reliability

**Async Optimization:**

- Apply ThreadPoolExecutor pattern to all remaining tools
- Implement connection pooling for better performance
- Add request queuing and rate limiting

**Error Handling:**

- Implement retry logic for transient failures
- Add health checks and automatic reconnection
- Graceful degradation when Neovim features unavailable

### 4. Configuration & Customization

**User Configuration:**

- Plugin configuration via `init.lua`/`init.vim`
- Customizable tool permissions and restrictions
- Configurable MCP server settings (port, auth, etc.)

**Tool Customization:**

- User-defined custom tools via Lua functions
- Tool filtering and whitelisting
- Context-aware tool suggestions

### 5. Integration & Ecosystem

**MCP Client Support:**

- Test with Claude Desktop integration
- Support for additional MCP clients
- WebSocket transport option for web-based clients

**Neovim Ecosystem:**

- Integration with popular plugins (telescope, nvim-tree, etc.)
- LSP client bridge for enhanced language support
- Terminal and job management tools

### Implementation Priority

1. **Phase 1**: Complete plugin mode implementation
1. **Phase 2**: Add core diagnostic and search tools
1. **Phase 3**: Performance optimization and advanced tools
1. **Phase 4**: Configuration system and ecosystem integration

The foundation is solid with working standalone mode and resolved async
conflicts. The architecture supports both modes with minimal code duplication,
making the plugin transition straightforward.
