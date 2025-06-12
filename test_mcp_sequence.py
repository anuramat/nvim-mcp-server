#!/usr/bin/env python3
"""Test proper nvimcp initialization sequence."""

import json
import sys
import subprocess
import time


def send_nvimcp_messages():
    """Send proper nvimcp initialization sequence."""

    # Start the server process
    proc = subprocess.Popen(
        [
            "nix",
            "develop",
            "--command",
            "python",
            "standalone.py",
            "--socket-path",
            "/tmp/nvim.sock",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Step 1: Send initialize request
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

        print("Sending initialize request...", file=sys.stderr)
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read response
        response_line = proc.stdout.readline()
        print(f"Initialize response: {response_line.strip()}", file=sys.stderr)

        # Step 2: Send initialized notification
        initialized_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        print("Sending initialized notification...", file=sys.stderr)
        proc.stdin.write(json.dumps(initialized_notif) + "\n")
        proc.stdin.flush()

        # Step 3: Now call a tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_status", "arguments": {}},
        }

        print("Sending tool call...", file=sys.stderr)
        proc.stdin.write(json.dumps(tool_request) + "\n")
        proc.stdin.flush()

        # Read tool response
        tool_response_line = proc.stdout.readline()
        print(f"Tool response: {tool_response_line.strip()}", file=sys.stderr)

        # Wait a bit then close
        time.sleep(1)
        proc.stdin.close()

        # Wait for process to finish
        stdout, stderr = proc.communicate(timeout=5)
        print(f"Final stdout: {stdout}", file=sys.stderr)
        print(f"Final stderr: {stderr}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    send_nvimcp_messages()
