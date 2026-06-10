"""Tests for the MCP stdio transport layer of scripts/mcp_server.py.

Claudity-original (the transport replaces FastMCP per PORTING.md R17, so
upstream has no equivalent tests). Drives the real server process over
stdin/stdout pipes with newline-delimited JSON-RPC and asserts on the
wire behavior: handshake and version negotiation, tool listing and
round-trips, error codes, silence on notifications, and stdout purity
(nothing but JSON-RPC ever reaches stdout).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "scripts" / "mcp_server.py"

EXPECTED_TOOLS = {
    "run_clarity",
    "check_decision",
    "get_packet_status",
    "read_protocol_document",
    "write_protocol_document",
    "record_decision",
    "record_failure",
    "record_suggestion",
}

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}


def run_server(messages: list[dict | str], project_dir: Path) -> list[dict]:
    """Feed messages to a fresh server process; return its stdout responses.

    Dict messages are JSON-encoded; string messages are sent raw (for
    malformed-input tests). Asserts stdout purity: every line must parse
    as JSON.
    """
    payload = "".join(
        (m if isinstance(m, str) else json.dumps(m)) + "\n" for m in messages
    )
    proc = subprocess.run(
        [sys.executable, str(SERVER)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        env={
            "CLAUDE_PROJECT_DIR": str(project_dir),
            "CLAUDITY_PLUGIN_ROOT": str(REPO),
            "PATH": "/usr/bin:/bin",
        },
    )
    responses = []
    for line in proc.stdout.splitlines():
        assert line.strip(), "blank line on stdout"
        responses.append(json.loads(line))  # raises -> stdout impurity
    return responses


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    from protocol_init import init_protocol

    (tmp_path / ".git").mkdir()  # git project -> hidden .clarity-protocol/ name
    init_protocol(tmp_path)
    return tmp_path


def handshake(*extra: dict | str, project_dir: Path) -> list[dict]:
    """Run the server with the standard handshake plus extra messages."""
    return run_server([INITIALIZE, INITIALIZED, *extra], project_dir)


class TestHandshake:
    def test_initialize_result(self, project: Path) -> None:
        (resp,) = handshake(project_dir=project)
        result = resp["result"]
        assert resp["id"] == 1
        assert result["protocolVersion"] == "2025-06-18"
        assert result["serverInfo"]["name"] == "clarity-agent"
        assert "tools" in result["capabilities"]
        assert "check_decision" in result["instructions"]

    def test_older_protocol_version_echoed(self, project: Path) -> None:
        init = dict(INITIALIZE, params=dict(INITIALIZE["params"], protocolVersion="2024-11-05"))
        (resp,) = run_server([init], project)
        assert resp["result"]["protocolVersion"] == "2024-11-05"

    def test_unknown_protocol_version_falls_back(self, project: Path) -> None:
        init = dict(INITIALIZE, params=dict(INITIALIZE["params"], protocolVersion="1999-01-01"))
        (resp,) = run_server([init], project)
        assert resp["result"]["protocolVersion"] == "2025-06-18"

    def test_notifications_get_no_response(self, project: Path) -> None:
        responses = handshake(project_dir=project)
        assert len(responses) == 1  # only the initialize result

    def test_ping(self, project: Path) -> None:
        ping = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        responses = handshake(ping, project_dir=project)
        assert responses[-1] == {"jsonrpc": "2.0", "id": 2, "result": {}}


class TestToolsList:
    def test_lists_exactly_the_eight_tools(self, project: Path) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        responses = handshake(req, project_dir=project)
        tools = responses[-1]["result"]["tools"]
        assert {t["name"] for t in tools} == EXPECTED_TOOLS

    def test_every_tool_has_description_and_schema(self, project: Path) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        responses = handshake(req, project_dir=project)
        for tool in responses[-1]["result"]["tools"]:
            assert tool["description"], f"{tool['name']} has no description"
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "required" in schema


class TestToolsCall:
    def _call(self, project: Path, name: str, arguments: dict, req_id: int = 2) -> dict:
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        return handshake(req, project_dir=project)[-1]

    def test_get_packet_status_round_trip(self, project: Path) -> None:
        resp = self._call(project, "get_packet_status", {})
        assert resp["result"]["isError"] is False
        assert resp["result"]["content"][0]["type"] == "text"

    def test_record_failure_creates_mailbox_item(self, project: Path) -> None:
        resp = self._call(
            project,
            "record_failure",
            {"title": "Token replay", "description": "Stolen token reused; user data leaks."},
        )
        assert resp["result"]["isError"] is False
        items = list((project / ".clarity-protocol" / "mailboxes" / "failure-brainstorm").glob("*.md"))
        assert len(items) == 1
        assert "**Source:** mcp" in items[0].read_text()

    def test_write_then_read_round_trip(self, project: Path) -> None:
        write = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "write_protocol_document",
                "arguments": {"document_path": "goal/problem.md", "content": "# P\n\nReal text.\n"},
            },
        }
        read = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "read_protocol_document",
                "arguments": {"document_path": "goal/problem.md"},
            },
        }
        responses = handshake(write, read, project_dir=project)
        assert "Written" in responses[-2]["result"]["content"][0]["text"]
        assert "Real text." in responses[-1]["result"]["content"][0]["text"]

    def test_missing_required_argument_is_tool_error(self, project: Path) -> None:
        resp = self._call(project, "record_failure", {"title": "no description"})
        assert resp["result"]["isError"] is True
        assert "description" in resp["result"]["content"][0]["text"]

    def test_unknown_tool_is_invalid_params(self, project: Path) -> None:
        resp = self._call(project, "no_such_tool", {})
        assert resp["error"]["code"] == -32602


class TestResources:
    def _req(self, req_id: int, method: str, params: dict | None = None) -> dict:
        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            req["params"] = params
        return req

    def test_capability_declared(self, project: Path) -> None:
        (resp,) = handshake(project_dir=project)
        assert "resources" in resp["result"]["capabilities"]

    def test_lists_three_concrete_resources(self, project: Path) -> None:
        responses = handshake(self._req(2, "resources/list"), project_dir=project)
        uris = {r["uri"] for r in responses[-1]["result"]["resources"]}
        assert uris == {"clarity://summary", "clarity://decisions", "clarity://behaviors"}

    def test_lists_three_templates(self, project: Path) -> None:
        responses = handshake(self._req(2, "resources/templates/list"), project_dir=project)
        templates = {t["uriTemplate"] for t in responses[-1]["result"]["resourceTemplates"]}
        assert templates == {
            "clarity://processes/{name}",
            "clarity://thinkers/{name}",
            "clarity://protocol/{path}",
        }

    def test_read_concrete_resource(self, project: Path) -> None:
        responses = handshake(
            self._req(2, "resources/read", {"uri": "clarity://summary"}),
            project_dir=project,
        )
        (content,) = responses[-1]["result"]["contents"]
        assert content["uri"] == "clarity://summary"
        assert content["mimeType"] == "text/markdown"
        assert content["text"].strip()

    def test_read_templated_protocol_document(self, project: Path) -> None:
        (project / ".clarity-protocol" / "goal" / "problem.md").write_text("# P\n\nReal.\n")
        responses = handshake(
            self._req(2, "resources/read", {"uri": "clarity://protocol/goal/problem.md"}),
            project_dir=project,
        )
        assert "Real." in responses[-1]["result"]["contents"][0]["text"]

    def test_read_templated_process_guide(self, project: Path) -> None:
        responses = handshake(
            self._req(2, "resources/read", {"uri": "clarity://processes/failure-analysis"}),
            project_dir=project,
        )
        text = responses[-1]["result"]["contents"][0]["text"]
        assert "# Failure Analysis" in text
        assert "${CLAUDE_PLUGIN_ROOT}" not in text  # placeholder substituted

    def test_traversal_guard(self, project: Path) -> None:
        responses = handshake(
            self._req(2, "resources/read", {"uri": "clarity://protocol/../../etc/passwd"}),
            project_dir=project,
        )
        assert "traversal" in responses[-1]["result"]["contents"][0]["text"].lower()

    def test_unknown_uri_is_resource_not_found(self, project: Path) -> None:
        responses = handshake(
            self._req(2, "resources/read", {"uri": "clarity://nope"}),
            project_dir=project,
        )
        assert responses[-1]["error"]["code"] == -32002


class TestProtocolErrors:
    def test_unknown_method(self, project: Path) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}
        responses = handshake(req, project_dir=project)
        assert responses[-1]["error"]["code"] == -32601

    def test_malformed_json(self, project: Path) -> None:
        responses = handshake("this is not json", project_dir=project)
        err = responses[-1]
        assert err["error"]["code"] == -32700
        assert err["id"] is None
