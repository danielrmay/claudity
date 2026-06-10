"""Tests for tools/brainstorm.py — brainstorm-specific tools and handler.

Vendored for Claudity from microsoft/clarity-agent@6b32c43
(tests/test_brainstorm_tools.py, MIT License, Copyright (c) Microsoft
Corporation). Modifications per PORTING.md: package imports become
sibling-module imports; tests of the dropped LLM-dispatch surface
(read_thinker_guide, create_brainstorm_handler, create_brainstorm_tools,
format_available_thinkers, recommend/read-guide tool schemas) are removed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from brainstorm import (
    RECORD_FAILURE_TOOL,
    ChainAnnotation,
    ChainStep,
    RawFailure,
    record_failure,
    render_chain_markdown,
    render_failure_markdown,
)

class TestRenderChainMarkdown:
    """render_chain_markdown() produces expected output."""

    def test_basic_chain(self) -> None:
        chain = [
            ChainStep(step_number=1, description="User submits form"),
            ChainStep(step_number=2, description="Server crashes"),
        ]
        md = render_chain_markdown(chain)
        assert "1. User submits form" in md
        assert "2. Server crashes" in md

    def test_harm_markers(self) -> None:
        chain = [
            ChainStep(step_number=1, description="Data exposed", harm_begins=True),
            ChainStep(step_number=2, description="Attacker downloads", harm_ends=True),
        ]
        md = render_chain_markdown(chain)
        assert "**harm begins**" in md
        assert "**harm ends**" in md

    def test_annotations(self) -> None:
        chain = [
            ChainStep(
                step_number=1,
                description="Request arrives",
                annotations=[
                    ChainAnnotation(type="intervention_point", content="Rate limit here"),
                    ChainAnnotation(type="observation", content="No auth check"),
                ],
            ),
        ]
        md = render_chain_markdown(chain)
        assert "*Intervention point:* Rate limit here" in md
        assert "*Observation:* No auth check" in md


class TestRenderFailureMarkdown:
    """render_failure_markdown() produces expected output."""

    def test_basic_failure(self) -> None:
        f = RawFailure(
            title="SQL Injection",
            source="security-thinker",
            description="Unsanitized input leads to data breach.",
        )
        md = render_failure_markdown(f)
        assert "# SQL Injection" in md
        assert "**Source:** security-thinker" in md
        assert "Unsanitized input" in md

    def test_pre_existing_flag(self) -> None:
        f = RawFailure(
            title="T", source="s", description="d", pre_existing=True,
        )
        md = render_failure_markdown(f)
        assert "**Pre-existing:** Yes" in md

    def test_pre_existing_false(self) -> None:
        f = RawFailure(
            title="T", source="s", description="d", pre_existing=False,
        )
        md = render_failure_markdown(f)
        assert "**Pre-existing:** No" in md

    def test_omits_pre_existing_when_none(self) -> None:
        f = RawFailure(title="T", source="s", description="d")
        md = render_failure_markdown(f)
        assert "Pre-existing" not in md

    def test_includes_chain_when_provided(self) -> None:
        f = RawFailure(
            title="T",
            source="s",
            description="d",
            failure_chain=[
                ChainStep(step_number=1, description="Step one"),
            ],
        )
        md = render_failure_markdown(f)
        assert "## Failure Chain" in md
        assert "1. Step one" in md

    def test_includes_additional_context(self) -> None:
        f = RawFailure(
            title="T", source="s", description="d",
            additional_context="Severity is high.",
        )
        md = render_failure_markdown(f)
        assert "## Additional Context" in md
        assert "Severity is high." in md


# ---------------------------------------------------------------------------
# record_failure (core function)
# ---------------------------------------------------------------------------

class TestRecordFailure:
    """record_failure() writes to the failure-brainstorm mailbox."""

    def test_writes_failure_to_mailbox(self, tmp_path: Path) -> None:
        pd = tmp_path / ".clarity-protocol"
        pd.mkdir()
        path, msg = record_failure(
            pd,
            title="Data Loss on Crash",
            description="Server crash causes data loss.",
        )
        assert path.exists()
        assert "Recorded failure" in msg

    def test_file_contains_rendered_content(self, tmp_path: Path) -> None:
        pd = tmp_path / ".clarity-protocol"
        pd.mkdir()
        path, _ = record_failure(
            pd,
            title="Auth Bypass",
            description="Missing auth check allows unauthorized access.",
            source="security-analysis",
            additional_context="Critical severity.",
        )
        content = path.read_text()
        assert "# Auth Bypass" in content
        assert "**Source:** security-analysis" in content
        assert "Missing auth check" in content
        assert "Critical severity." in content

    def test_pre_existing_marker_in_message(self, tmp_path: Path) -> None:
        pd = tmp_path / ".clarity-protocol"
        pd.mkdir()
        _, msg = record_failure(
            pd,
            title="T",
            description="d",
            pre_existing=True,
        )
        assert "(pre-existing)" in msg

    def test_failure_chain_parsing(self, tmp_path: Path) -> None:
        pd = tmp_path / ".clarity-protocol"
        pd.mkdir()
        raw_chain: list[dict[str, Any]] = [
            {"step_number": 1, "description": "User clicks button"},
            {
                "step_number": 2,
                "description": "Service fails",
                "harm_begins": True,
                "annotations": [
                    {"type": "intervention_point", "content": "Add retry"},
                ],
            },
        ]
        path, _ = record_failure(
            pd,
            title="Cascading Failure",
            description="Click triggers cascade.",
            failure_chain=raw_chain,
        )
        content = path.read_text()
        assert "## Failure Chain" in content
        assert "User clicks button" in content
        assert "**harm begins**" in content
        assert "*Intervention point:*" in content

    def test_multiple_failures_create_separate_files(self, tmp_path: Path) -> None:
        pd = tmp_path / ".clarity-protocol"
        pd.mkdir()
        p1, _ = record_failure(pd, title="Failure One", description="d1")
        p2, _ = record_failure(pd, title="Failure Two", description="d2")
        assert p1 != p2
        assert p1.exists()
        assert p2.exists()


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

class TestToolSchemas:
    """Tool schemas are well-formed."""

    @pytest.mark.parametrize("tool", [
        RECORD_FAILURE_TOOL,
    ])
    def test_has_name_and_schema(self, tool: dict[str, Any]) -> None:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert "required" in tool["input_schema"]
