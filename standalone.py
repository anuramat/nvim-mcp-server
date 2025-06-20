#!/usr/bin/env python3
"""Standalone nvimcp server."""

import argparse
import asyncio
import logging
import sys
from nvimcp.connection import connect_neovim, ConnectionError
from nvimcp.core import NvimcpServer


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Nvimcp Server")
    parser.add_argument(
        "--mode",
        choices=["auto", "socket", "embedded"],
        default="auto",
        help="Connection mode (default: auto)",
    )
    parser.add_argument(
        "--socket-path",
        default="/tmp/nvim.sock",
        help="Socket path for socket mode (default: /tmp/nvim.sock)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting nvimcp server")

    try:
        # Connect to Neovim
        logger.info(f"Connecting to nvim (mode: {args.mode})")
        nvim = connect_neovim(mode=args.mode, socket_path=args.socket_path)

        # Create and run MCP server
        server = NvimcpServer(nvim)
        logger.info("nvimcp server ready")

        # Run MCP server
        await server.run()

    except ConnectionError as e:
        logger.error(f"Failed to connect to nvim: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        import traceback

        logger.error(f"Unexpected error: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
