"""Unicode survives the protocol's file I/O on every platform.

Claudity-original Windows-compat regression tests (issue #6): Windows'
locale default encoding is cp1252, so any read_text()/write_text()/open()
without encoding="utf-8" corrupts (or crashes on) unicode markdown. These
round-trips push em-dashes, emoji, CJK, and accented text through every
recording path and the status engine, asserting byte-faithful utf-8 on the
way out. On the windows-latest CI job this is the empirical proof; do not
"fix" a failure here by setting PYTHONUTF8 in CI — that masks exactly the
bugs this guards against.
"""

from __future__ import annotations

from pathlib import Path

import pytest

UNICODE_SAMPLE = "Touché — flag flips silently 🚩; 利用者は気づかない (no-one notices)"


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    from protocol_init import init_protocol

    (tmp_path / ".git").mkdir()
    init_protocol(tmp_path)
    return tmp_path


@pytest.fixture()
def proto(project: Path) -> Path:
    return project / ".clarity-protocol"


class TestRecordingPaths:
    def test_record_failure_round_trip(self, proto: Path) -> None:
        from brainstorm import record_failure

        path, _ = record_failure(
            proto,
            title="Touché — silent flip 🚩",
            description=UNICODE_SAMPLE,
            additional_context="Sévérité: haute — 重大",
        )
        text = path.read_text(encoding="utf-8")
        assert UNICODE_SAMPLE in text
        assert "Touché — silent flip 🚩" in text

    def test_record_suggestion_round_trip(self, proto: Path) -> None:
        from suggestion import record_suggestion

        path, _ = record_suggestion(
            proto,
            title="Añadir partes interesadas",
            target_document="goal/stakeholders.md",
            suggestion=UNICODE_SAMPLE,
        )
        assert UNICODE_SAMPLE in path.read_text(encoding="utf-8")

    def test_mailbox_config_round_trip(self, proto: Path) -> None:
        from mailbox import Mailbox

        mb = Mailbox.create(proto, "unicode-box", {
            "display_name": "boîte à idées — 提案箱",
            "collector": "review",
            "collector_type": "batch",
        })
        assert mb.load_config()["display_name"] == "boîte à idées — 提案箱"


class TestServerPaths:
    def test_write_then_read_protocol_document(self, project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        from mcp_server import read_protocol_document, write_protocol_document

        write_protocol_document("goal/problem.md", f"# Problème\n\n{UNICODE_SAMPLE}\n")
        assert UNICODE_SAMPLE in read_protocol_document("goal/problem.md")

    def test_record_decision_round_trip(self, project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        from mcp_server import record_decision

        record_decision(
            title="Choisir SQLite — 単一ノード",
            context=UNICODE_SAMPLE,
            decision="SQLite.",
            rationale="Simplicité 🎯",
        )
        (decision_file,) = (project / ".clarity-protocol" / "decisions").glob("decision-01-*.md")
        text = decision_file.read_text(encoding="utf-8")
        assert UNICODE_SAMPLE in text
        assert "Simplicité 🎯" in text


class TestStatusEngine:
    def test_status_reads_unicode_documents(self, proto: Path) -> None:
        from protocol_status import check_packet_status, format_for_agent, record_hashes

        (proto / "goal" / "problem.md").write_text(
            f"# Problème\n\n{UNICODE_SAMPLE}\n", encoding="utf-8"
        )
        record_hashes(proto, ["goal/problem.md"])
        report = check_packet_status(proto)
        assert report["documents"]["goal/problem.md"]["status"] == "current"
        format_for_agent(report)  # must not raise on unicode content
