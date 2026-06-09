#!/usr/bin/env python3
"""
Initialize a protocol directory for a project.

Creates the directory structure, config.json, and template files.

Vendored for Claudity from microsoft/clarity-agent@6b32c43
(src/clarity_agent/protocol/initialize.py, MIT License,
Copyright (c) Microsoft Corporation). Modifications per PORTING.md:
the protocol-dir resolution is inlined so the file runs standalone;
the AGENTS.md snippet refresh and mailbox/suggestion-box creation are
removed (Claudity installs its snippet into CLAUDE.md via the embed
command, and replaces async mailboxes with parallel subagents); the
default config identifies Claudity instead of a clarity-agent install.

Template contents are verbatim from upstream — their placeholder text
must keep matching TEMPLATE_MARKERS in protocol_status.py, which is how
freshly-initialized documents are detected as "empty".
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Protocol directory resolution (inlined from clarity_agent.app_paths)
# ---------------------------------------------------------------------------

_PROTOCOL_DIR_DOT = ".clarity-protocol"
_PROTOCOL_DIR_VISIBLE = "Clarity Protocol"


def _resolve_protocol_dir(project_dir: Path) -> Path:
    """Return the protocol directory for a project.

    Existing projects keep whichever name they already use. For new projects,
    git repositories get the hidden name; non-git directories the visible one.
    """
    dot = project_dir / _PROTOCOL_DIR_DOT
    visible = project_dir / _PROTOCOL_DIR_VISIBLE
    if dot.exists():
        return dot
    if visible.exists():
        return visible
    if (project_dir / ".git").exists():
        return dot
    return visible


# ---------------------------------------------------------------------------
# Default config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, object] = {
    "claudity": {
        "version": "0.1.0",
    },
    "thinkers": {
        "disabled": [],
        "custom": [],
    },
    "processes": {
        "custom": [],
    },
}


# ---------------------------------------------------------------------------
# Template files
# ---------------------------------------------------------------------------

# Keys are paths relative to .clarity-protocol/.
# Values are the file contents (minimal templates that clearly indicate
# they need to be filled in).
TEMPLATES: dict[str, str] = {
    "summary.md": """\
# [Project Title]

[Write this like you're telling a friend about something you're excited to work on. \
What's the problem that got you fired up? What's the idea? Why does it matter? \
Keep it to a few short paragraphs — enough to make someone care, not enough to bore them.]
""",
    "goal/problem.md": """\
# Problem Statement

[To be determined. Run problem clarification to develop this.]

## Why This Matters

[TBD]

## Success Criteria

[TBD]
""",
    "goal/stakeholders.md": """\
# Stakeholders

[To be determined. Run problem clarification to identify stakeholders.]
""",
    "goal/requirements.md": """\
# Requirements

[To be determined. Run problem clarification to extract requirements.]
""",
    "goal/open-questions.md": """\
# Open Questions

No open questions have been identified yet. Problem clarification will assess whether there are \
fundamental unknowns that would change the solution approach.
""",
    "goal/resolved-questions.md": """\
# Resolved Questions

No questions have been resolved yet. When open questions are resolved, they are moved here \
with their findings and resolution.
""",
    "solution/solution.md": """\
# Solution

[To be determined. Run solution brainstorming to develop this.]
""",
    "solution/architecture.md": """\
# Architecture

[To be determined. Run architecture design to develop this.]
""",
    "solution/solution-summary.md": """\
# Solution Summary

[To be determined. This summary is generated during solution brainstorming \
and updated during architecture design.]
""",
    "failures/failures.md": """\
# Failure Modes

No failure modes have been analyzed yet. Run failure analysis to begin identifying potential failures.
""",
    "decisions/decisions.md": """\
# Decisions

No decisions have been recorded yet. As important choices arise, they will be documented here.
""",
    "notes.md": """\
# Notes

[To be determined. Guiding principles and cross-phase observations will be added here as the \
project develops. Items tagged `[for: <phase>]` are actionable observations for a specific phase; \
untagged items are permanent guiding principles.]
""",
    "observations.md": """\
# Observations

No observations have been recorded yet. As failure analysis and other processes surface \
interesting patterns, coverage notes, and provenance details, they will be logged here.
""",
}


# ---------------------------------------------------------------------------
# Core operation
# ---------------------------------------------------------------------------

def init_protocol(project_dir: Path) -> Path:
    """Initialize the protocol directory in *project_dir*.

    Creates the directory structure, config.json, and template files.
    Skips files that already exist (safe to run on a partially-initialized
    project).

    Returns the path to the protocol directory.
    """
    protocol_dir: Path = _resolve_protocol_dir(project_dir)

    # Create directory structure
    for template_path in TEMPLATES:
        (protocol_dir / template_path).parent.mkdir(parents=True, exist_ok=True)

    # Write config.json
    config_path: Path = protocol_dir / "config.json"
    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
            f.write("\n")

    # Write template files
    for rel_path, content in TEMPLATES.items():
        full_path: Path = protocol_dir / rel_path
        if not full_path.exists():
            full_path.write_text(content, encoding="utf-8")

    return protocol_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Initialize a .clarity-protocol/ directory for a project",
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)",
    )

    args: argparse.Namespace = parser.parse_args()

    project_dir: Path = Path(args.project_dir).resolve()
    if not project_dir.exists():
        parser.error(f"Project directory does not exist: {project_dir}")

    protocol_dir: Path = init_protocol(project_dir)
    print(f"Initialized {protocol_dir.relative_to(project_dir)}/")


if __name__ == "__main__":
    main()
