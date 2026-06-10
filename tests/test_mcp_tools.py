"""Tests for the Clarity Agent MCP server.

Verifies that all tools are registered and that the core tools produce
sensible output when pointed at test fixtures.

Vendored for Claudity from microsoft/clarity-agent@6b32c43
(tests/test_mcp_server.py, MIT License, Copyright (c) Microsoft
Corporation). Modifications per PORTING.md (R17): package imports become
sibling-module imports; CLARITY_PROJECT_DIR becomes CLAUDE_PROJECT_DIR;
registration tests inspect the stdlib server's TOOLS table instead of
FastMCP managers; tests of the descoped internal functions and MCP
resources are removed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def empty_project(tmp_path: Path) -> Path:
    """Return a temp directory with no protocol."""
    return tmp_path


@pytest.fixture()
def initialized_project(tmp_path: Path) -> Path:
    """Return a temp directory with an initialized protocol."""
    from protocol_init import init_protocol
    init_protocol(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _set_project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLAUDE_PROJECT_DIR for each test so tools resolve correctly."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("CLARITY_PROJECT_DIR", raising=False)


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

def test_all_tools_registered() -> None:
    """All expected MCP tools should be registered."""
    from mcp_server import TOOLS

    tool_names = {t["name"] for t in TOOLS}
    expected = {
        "run_clarity",
        "check_decision",
        "get_packet_status",
        "read_protocol_document",
        "write_protocol_document",
        "record_decision",
        "record_failure",
        "record_suggestion",
    }
    assert expected == tool_names, (
        f"Missing tools: {expected - tool_names}\n"
        f"Extra tools: {tool_names - expected}"
    )


def test_no_internal_tools_exposed() -> None:
    """Internal functions should NOT be registered as MCP tools."""
    from mcp_server import TOOLS

    tool_names = {t["name"] for t in TOOLS}
    internal = {
        "init_protocol",
        "list_protocol_documents",
        "record_packet_status",
        "get_next_action",
        "list_processes",
        "read_process_guide",
        "list_thinkers",
        "read_thinker_guide",
        "read_behaviors",
        "generate_packet",
        "get_mailbox_status",
        "check_failure_state",
        "snapshot_mailbox",
        "list_mailbox_items",
        "read_mailbox_item",
        "archive_mailbox_item",
    }
    leaked = internal & tool_names
    assert not leaked, f"Internal functions leaked as MCP tools: {leaked}"


# ---------------------------------------------------------------------------
# MCP Tool function tests
# ---------------------------------------------------------------------------

class TestRunClarity:
    def test_new_project(self, empty_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(empty_project))
        from mcp_server import run_clarity
        result = run_clarity()
        assert "New Project" in result

    def test_existing_project(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import run_clarity
        result = run_clarity()
        assert "New Project" not in result

    def test_inlines_process_guide(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When a next action has a process, the guide content is inlined."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import run_clarity
        result = run_clarity()
        if "Process Guide:" in result:
            assert "##" in result


class TestCheckDecision:
    def test_no_protocol(self, empty_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(empty_project))
        from mcp_server import check_decision
        result = check_decision("Add a new database")
        assert "No protocol" in result

    def test_returns_context(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import check_decision, write_protocol_document
        write_protocol_document("goal/requirements.md", "# Requirements\n\nMust be fast.")
        result = check_decision("Switch to a slow database")
        assert "Requirements" in result
        assert "Proposed Change" in result

    def test_with_decisions(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import check_decision, record_decision
        record_decision(
            title="Use PostgreSQL",
            context="Need a database.",
            decision="Use PostgreSQL.",
            rationale="Battle-tested.",
        )
        result = check_decision("Switch to MongoDB")
        assert "Existing Decisions" in result

    def test_empty_protocol(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import check_decision
        result = check_decision("Add a cache layer")
        assert "No decisions" in result or "Proceed" in result


class TestGetPacketStatus:
    def test_no_protocol(self, empty_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(empty_project))
        from mcp_server import get_packet_status
        result = get_packet_status()
        assert "No protocol" in result

    def test_returns_report(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import get_packet_status
        result = get_packet_status()
        assert "Packet Status" in result or "empty" in result.lower() or "missing" in result.lower()

    def test_json_format(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import get_packet_status
        result = get_packet_status(output_format="json")
        parsed = json.loads(result)
        assert "documents" in parsed


class TestReadWriteProtocolDocument:
    def test_read_nonexistent(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import read_protocol_document
        result = read_protocol_document("nonexistent.md")
        assert "not found" in result.lower()

    def test_write_and_read(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import read_protocol_document, write_protocol_document

        write_result = write_protocol_document("goal/problem.md", "# Test Problem\n\nThis is a test.")
        assert "Written" in write_result

        read_result = read_protocol_document("goal/problem.md")
        assert "Test Problem" in read_result

    def test_path_traversal_blocked(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import read_protocol_document
        result = read_protocol_document("../../etc/passwd")
        assert "traversal" in result.lower()

    def test_write_auto_records_hashes(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Writing a protocol document should auto-record its content hash."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import write_protocol_document
        write_protocol_document("goal/problem.md", "# Real Problem\n\nA real problem statement.")
        from mailbox import protocol_dir
        from protocol_status import load_config
        config = load_config(protocol_dir(initialized_project))
        state = config.get("documentState", {})
        assert "goal/problem.md" in state


class TestRecordDecision:
    def test_records_decision(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import record_decision
        result = record_decision(
            title="Use Python for MCP server",
            context="Need to choose implementation language.",
            decision="Use Python with FastMCP.",
            rationale="Existing codebase is Python.",
        )
        assert "Recorded decision" in result
        assert "decisions/" in result

    def test_state_keyed_by_full_stem(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Claudity R17 deviation: decisionState key matches the guide CLI's
        decision-NN-<slug> ids, so tool and CLI never double-record."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mailbox import protocol_dir
        from mcp_server import record_decision
        from protocol_status import load_config
        record_decision(
            title="Use SQLite",
            context="Need storage.",
            decision="SQLite.",
            rationale="Single node.",
        )
        state = load_config(protocol_dir(initialized_project)).get("decisionState", {})
        (key,) = state.keys()
        assert key == "decision-01-use-sqlite", key


class TestRecordFailure:
    def test_records_failure(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import record_failure
        result = record_failure(
            title="Test failure",
            description="Something could go wrong with testing.",
        )
        assert "Recorded failure" in result

    def test_source_reaches_mailbox_item(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Claudity R17 deviation: optional source preserves thinker/human provenance."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mailbox import protocol_dir
        from mcp_server import record_failure
        record_failure(
            title="Token replay",
            description="Stolen token reused; user data leaks.",
            source="security-thinker",
        )
        box = protocol_dir(initialized_project) / "mailboxes" / "failure-brainstorm"
        (item,) = list(box.glob("*.md"))
        assert "**Source:** security-thinker" in item.read_text()


class TestRecordSuggestion:
    def test_records_suggestion(self, initialized_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(initialized_project))
        from mcp_server import record_suggestion
        result = record_suggestion(
            title="Add stakeholder",
            target_document="goal/stakeholders.md",
            suggestion="Consider adding end users as stakeholders.",
        )
        assert "Recorded suggestion" in result
