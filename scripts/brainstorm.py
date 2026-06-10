"""Failure brainstorming tools.

Provides tools for the failure-brainstorming process: recording failure
modes, recommending specialist thinkers for deeper analysis, and reading
thinker methodology guides.

Vendored for Claudity from microsoft/clarity-agent@6b32c43
(src/clarity_agent/ai_actions/brainstorm.py, MIT License,
Copyright (c) Microsoft Corporation). Modifications per PORTING.md:
the LLM-dispatch surface is dropped (create_brainstorm_handler,
create_brainstorm_tools, format_available_thinkers, read_thinker_guide,
the recommend_deeper_analysis/read_thinker_guide tool schemas, and the
recommend-deeper/read-thinker-guide CLI subcommands) — Claudity runs
thinkers as Claude Code subagents (R9). The clarity_agent package
imports become sibling-module imports (mailbox).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mailbox import Mailbox, find_protocol_dir

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ChainAnnotation:
    """An annotation on a failure chain step."""

    type: str  # "intervention_point", "observation", "branch_point"
    content: str


@dataclass
class ChainStep:
    """A single step in a failure chain."""

    step_number: int
    description: str
    annotations: list[ChainAnnotation] = field(default_factory=list)
    harm_begins: bool = False
    harm_ends: bool = False


@dataclass
class RawFailure:
    """A single raw failure mode captured during analysis."""

    title: str
    source: str
    description: str
    additional_context: str = ""
    failure_chain: list[ChainStep] = field(default_factory=list)
    pre_existing: bool | None = None


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

RECORD_FAILURE_TOOL: dict[str, Any] = {
    "name": "record_failure",
    "description": (
        "Record a potential failure mode discovered during analysis. "
        "Call this once for each distinct failure mode you identify."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short descriptive title of what could go wrong",
            },
            "description": {
                "type": "string",
                "description": (
                    "1-3 sentences: what goes wrong, how it happens, "
                    "and who is harmed. Must end in actual harm."
                ),
            },
            "additional_context": {
                "type": "string",
                "description": (
                    "Optional: more detail about severity, related concerns, "
                    "initial thoughts on the failure chain"
                ),
            },
            "pre_existing": {
                "type": "boolean",
                "description": (
                    "Optional: true if this failure also exists (at similar "
                    "or greater severity) in the world before this solution "
                    "is implemented. Helps triage during analysis."
                ),
            },
            "failure_chain": {
                "type": "array",
                "description": (
                    "Optional annotated failure chain — a sequence of "
                    "steps describing how this failure unfolds. Include "
                    "this when you can see the chain of events clearly. "
                    "Each step can be annotated with intervention points, "
                    "observations, branch points, and harm boundary markers."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "step_number": {
                            "type": "integer",
                            "description": "Step number in the chain (1-based)",
                        },
                        "description": {
                            "type": "string",
                            "description": "What happens at this step",
                        },
                        "annotations": {
                            "type": "array",
                            "description": (
                                "Intervention points, observations, or "
                                "branch points on this step"
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "intervention_point",
                                            "observation",
                                            "branch_point",
                                        ],
                                        "description": "Type of annotation",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The annotation text",
                                    },
                                },
                                "required": ["type", "content"],
                            },
                        },
                        "harm_begins": {
                            "type": "boolean",
                            "description": "True if harm begins at this step",
                        },
                        "harm_ends": {
                            "type": "boolean",
                            "description": "True if harm ends at this step",
                        },
                    },
                    "required": ["step_number", "description"],
                },
            },
        },
        "required": ["title", "description"],
    },
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_ANNOTATION_LABELS: dict[str, str] = {
    "intervention_point": "Intervention point",
    "observation": "Observation",
    "branch_point": "Branch point",
}


def render_chain_markdown(chain: list[ChainStep]) -> str:
    """Render a failure chain to markdown.

    Produces numbered steps with inline annotations, harm boundary
    markers, and indented sub-items for intervention points,
    observations, and branch points.
    """
    parts: list[str] = []
    for step in chain:
        desc: str = step.description
        if step.harm_begins:
            desc += " **harm begins**"
        if step.harm_ends:
            desc += " **harm ends**"
        parts.append(f"{step.step_number}. {desc}\n")

        for ann in step.annotations:
            label: str = _ANNOTATION_LABELS.get(ann.type, ann.type)
            parts.append(f"   - *{label}:* {ann.content}\n")

    return "".join(parts)


def render_failure_markdown(failure: RawFailure) -> str:
    """Render a RawFailure as markdown content for a mailbox file."""
    parts: list[str] = [
        f"# {failure.title}\n\n",
        f"**Source:** {failure.source}\n",
    ]
    if failure.pre_existing is not None:
        label: str = "Yes" if failure.pre_existing else "No"
        parts.append(f"**Pre-existing:** {label}\n")
    parts.append(f"\n{failure.description}\n")
    if failure.failure_chain:
        parts.append(
            f"\n## Failure Chain\n\n"
            f"{render_chain_markdown(failure.failure_chain)}"
        )
    if failure.additional_context:
        parts.append(
            f"\n## Additional Context\n\n"
            f"{failure.additional_context}\n"
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Core functions (shared by handler and CLI)
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str, max_len: int = 50) -> str:
    """Convert a title to a filename-safe slug."""
    slug: str = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:max_len]


def _parse_chain(raw_chain: list[dict[str, Any]]) -> list[ChainStep]:
    """Parse a failure chain from tool call input into ChainStep objects."""
    steps: list[ChainStep] = []
    for raw_step in raw_chain:
        annotations: list[ChainAnnotation] = [
            ChainAnnotation(type=a["type"], content=a["content"])
            for a in raw_step.get("annotations", [])
        ]
        steps.append(ChainStep(
            step_number=raw_step["step_number"],
            description=raw_step["description"],
            annotations=annotations,
            harm_begins=raw_step.get("harm_begins", False),
            harm_ends=raw_step.get("harm_ends", False),
        ))
    return steps


FAILURE_MAILBOX_NAME: str = "failure-brainstorm"


def record_failure(
    protocol_dir: Path,
    title: str,
    description: str,
    *,
    source: str = "conversation",
    additional_context: str = "",
    pre_existing: bool | None = None,
    failure_chain: list[dict[str, Any]] | None = None,
) -> tuple[Path, str]:
    """Record a failure mode to the failure-brainstorm mailbox.

    Returns (path, confirmation_message).
    """
    chain: list[ChainStep] = _parse_chain(failure_chain) if failure_chain else []
    raw = RawFailure(
        title=title,
        source=source,
        description=description,
        additional_context=additional_context,
        failure_chain=chain,
        pre_existing=pre_existing,
    )
    content: str = render_failure_markdown(raw)

    mailbox_config: dict[str, Any] = {
        "display_name": "failure brainstorming",
        "collector": "failure-analysis",
        "collector_type": "batch",
        "status": "collecting",
    }
    mailbox: Mailbox = Mailbox.open_or_create(
        protocol_dir, FAILURE_MAILBOX_NAME, mailbox_config,
    )

    slug: str = _slugify(title)
    path: Path = mailbox.write(slug, content)

    pre_marker = " (pre-existing)" if pre_existing else ""
    return path, f"Recorded failure: {title}{pre_marker}"


# ---------------------------------------------------------------------------
# CLI entry point (for SDK/Bash path)
# ---------------------------------------------------------------------------

def _find_protocol_dir() -> Path:
    """Locate the protocol directory from cwd, walking up if needed."""
    return find_protocol_dir()


def _cli_main() -> None:
    """CLI: python3 scripts/brainstorm.py <command> < input.json

    All paths are auto-discovered from the working directory.
    No flags required.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 scripts/brainstorm.py",
        description="Brainstorm tools CLI. Reads JSON from stdin.",
    )
    sub = parser.add_subparsers(dest="command")

    # record-failure
    sub.add_parser("record-failure", help="Record a failure mode (JSON on stdin)")

    args = parser.parse_args()

    if args.command == "record-failure":
        data: dict[str, Any] = json.load(sys.stdin)
        path, msg = record_failure(
            _find_protocol_dir(),
            title=data["title"],
            description=data["description"],
            source=data.get("source", "conversation"),
            additional_context=data.get("additional_context", ""),
            pre_existing=data.get("pre_existing"),
            failure_chain=data.get("failure_chain"),
        )
        print(msg)
        print(f"Path: {path}")

    else:
        parser.error("a command is required")


if __name__ == "__main__":
    _cli_main()
