#!/usr/bin/env python3
"""SPIKE STUB — minimal MCP stdio server to validate plugin MCP behavior.

Validates (before the real port): headless -p support, tool-name prefix,
subagent visibility, CLAUDE_PROJECT_DIR / CLAUDE_PLUGIN_ROOT plumbing.
Replaced by the vendored clarity-agent server in a later commit.
"""

from __future__ import annotations

import json
import os
import sys

SUPPORTED_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

TOOLS = [
    {
        "name": "clarity_ping",
        "description": "Spike probe: returns pong plus the server's environment view.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    }
]


def _result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _handle(req):
    method = req.get("method")
    req_id = req.get("id")
    if method == "initialize":
        client_version = (req.get("params") or {}).get("protocolVersion", "")
        version = client_version if client_version in SUPPORTED_VERSIONS else "2025-06-18"
        return _result(req_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "clarity-agent", "version": "0.0.0-spike"},
        })
    if method == "ping":
        return _result(req_id, {})
    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})
    if method == "resources/list":
        return _result(req_id, {"resources": []})
    if method == "tools/call":
        name = (req.get("params") or {}).get("name")
        if name != "clarity_ping":
            return _result(req_id, {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            })
        text = (
            "pong"
            f" project_dir={os.environ.get('CLAUDE_PROJECT_DIR', '<unset>')}"
            f" plugin_root={os.environ.get('CLAUDITY_PLUGIN_ROOT', '<unset>')}"
            f" cwd={os.getcwd()}"
        )
        return _result(req_id, {"content": [{"type": "text", "text": text}], "isError": False})
    return _error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        if "id" not in req:  # notification — never respond
            continue
        sys.stdout.write(json.dumps(_handle(req)) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
