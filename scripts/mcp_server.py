#!/usr/bin/env python3
"""Clarity Agent MCP Server.

Exposes the clarity-agent process as MCP tools. The tool surface is
intentionally small: a coding agent needs only a handful of tools to
integrate clarity into its workflow.

Vendored for Claudity from microsoft/clarity-agent@6b32c43
(src/clarity_agent/mcp/server.py, MIT License,
Copyright (c) Microsoft Corporation). Modifications per PORTING.md (R17):

- The FastMCP framework is replaced by a hand-rolled stdlib JSON-RPC 2.0
  stdio loop (bottom of this file) so the plugin stays dependency-free.
  Tool docstrings become tool descriptions; the FastMCP ``instructions``
  string is served verbatim from ``initialize``.
- Project-dir resolution prefers ``CLAUDE_PROJECT_DIR`` (set by Claude
  Code in the spawned server's environment), keeping upstream's
  ``CLARITY_PROJECT_DIR`` and cwd as fallbacks.
- Agent-dir resolution targets the plugin layout via the
  ``CLAUDITY_PLUGIN_ROOT`` env var (injected by .mcp.json); process
  guides map to skill bodies via GUIDE_MAP. Served guide text has YAML
  frontmatter stripped and ``${CLAUDE_PLUGIN_ROOT}`` substituted with
  the real plugin root, since env expansion does not happen inside
  tool results.
- The clarity_agent package imports become sibling-module imports
  (protocol_status, brainstorm, suggestion, mailbox).
- Upstream's internal (non-tool) functions are descoped (no Claude Code
  consumer).
- The six MCP resources are served (``resources/list``,
  ``resources/templates/list``, ``resources/read``) so they stay
  @-mentionable in Claude Code. ``clarity://behaviors`` reads the
  claudity-begin/end block from the project's CLAUDE.md (upstream reads
  AGENTS.md and refreshes it via ``ensure_for_project``; resource reads
  here are side-effect-free). ``clarity://thinkers/{name}`` serves
  ``agents/<name>.md`` with the Claude Code frontmatter stripped.

Extensions beyond upstream's tool surface — protocol improvements, not
porting substitutions; upstream proposal candidates (PORTING.md "Server
extensions"):

- ``record_failure`` / ``record_suggestion`` accept an optional ``source``
  (upstream hardcodes source="mcp"): the orchestrator records on behalf
  of thinker subagents and human contributors, so provenance must travel
  through the tool call — upstream preserved it via per-thinker mailbox
  writers instead.
- ``record_decision`` accepts an optional ``related_docs`` (upstream's
  tool records no grounding): without related docs the staleness engine
  can never flag the decision for reconsideration.
- ``record_decision`` tracks state under the decision file's full stem
  (``decision-NN-<slug>``) instead of upstream's bare number prefix, so
  the tool and the decision-guidance CLI step write the same
  ``decisionState`` key instead of double-recording.
- The path-traversal guards use ``Path.is_relative_to`` instead of
  upstream's string-prefix comparison, which a sibling directory like
  ``.clarity-protocol-evil`` passes on any OS and case-insensitive
  filesystems weaken further.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent

from mailbox import protocol_dir as _protocol_dir_for  # noqa: E402

SERVER_NAME = "clarity-agent"

SERVER_INSTRUCTIONS = (
    "Clarity Agent provides structured thinking about what you're "
    "building, why, and what could go wrong. "
    "IMPORTANT: Before making architectural decisions (new services, "
    "auth/trust models, data schemas, external integrations, "
    "significant API contracts), call check_decision with a "
    "description of what you plan to do. "
    "Call run_clarity when starting work on a project or returning "
    "after a break. "
    "After completing significant implementation, call "
    "get_packet_status to check if protocol documents need updating."
)

# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------


def _resolve_project_dir(project_dir: str | None = None) -> Path:
    """Resolve the project directory from argument, env var, or cwd."""
    if project_dir:
        return Path(project_dir).resolve()
    for var in ("CLAUDE_PROJECT_DIR", "CLARITY_PROJECT_DIR"):
        env = os.environ.get(var)
        if env:
            return Path(env).resolve()
    return Path.cwd()


def _resolve_protocol_dir(project_dir: str | None = None) -> Path:
    """Resolve the protocol directory for a project."""
    return _protocol_dir_for(_resolve_project_dir(project_dir))


def _resolve_agent_dir() -> Path:
    """Resolve the Claudity plugin root (the agent-dir equivalent).

    ``CLAUDITY_PLUGIN_ROOT`` is injected via .mcp.json; the fallback
    covers direct invocation (the server lives in ``<root>/scripts/``).
    """
    env = os.environ.get("CLAUDITY_PLUGIN_ROOT")
    if env:
        return Path(env).resolve()
    return _SCRIPTS_DIR.parent


def _server_version() -> str:
    """Read the plugin version from the manifest (best effort)."""
    manifest = _resolve_agent_dir() / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("version", "0.0.0")
    except (OSError, json.JSONDecodeError):
        return "0.0.0"


# Process-guide names -> plugin paths. Guides with a 1:1 user entry are
# packaged as skills (R16); the rest live under skills/start/processes/.
GUIDE_MAP: dict[str, str] = {
    "clarity-agent": "skills/start/SKILL.md",
    "decision-guidance": "skills/decide/SKILL.md",
    "failure-brainstorming": "skills/risks/SKILL.md",
    "message-clarification": "skills/message/SKILL.md",
}

_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def _guide_text(process_name: str) -> str | None:
    """Read a process guide from the plugin, ready to serve.

    Strips YAML frontmatter and substitutes ``${CLAUDE_PLUGIN_ROOT}``
    with the real plugin root (env vars are not expanded inside tool
    results, so commands in served text must carry absolute paths).
    """
    agent_dir = _resolve_agent_dir()
    rel = GUIDE_MAP.get(process_name, f"skills/start/processes/{process_name}.md")
    guide_path = agent_dir / rel
    if not guide_path.exists():
        return None
    text = guide_path.read_text(encoding="utf-8")
    text = _FRONTMATTER_RE.sub("", text, count=1)
    return text.replace("${CLAUDE_PLUGIN_ROOT}", str(agent_dir))


# ===================================================================
# MCP TOOLS (8 tools — the coding agent surface)
# ===================================================================


def run_clarity(project_dir: str | None = None) -> str:
    """Assess project state and recommend what to work on next.

    This is the main entry point. Call this when starting work on a project,
    returning after a break, or when unsure what to do next. It checks whether
    a clarity protocol exists, evaluates document staleness, and returns a
    structured assessment with the recommended next process to follow.

    Auto-initializes the protocol if it doesn't exist yet.
    """
    proto_dir = _resolve_protocol_dir(project_dir)

    if not proto_dir.exists():
        guide = _guide_text("clarity-agent") or ""
        return (
            "# New Project\n\n"
            "No clarity protocol found. This is a new project.\n\n"
            "Follow the clarity-agent process guide below to get started.\n\n"
            "---\n\n" + guide
        )

    from protocol_status import (
        check_decision_triggers,
        check_packet_status,
        check_process_availability,
        format_for_agent,
        next_action,
    )

    report = check_packet_status(proto_dir)
    action = next_action(report)
    phases = check_process_availability(report)
    dreport = check_decision_triggers(proto_dir)

    status_text = format_for_agent(report)

    if dreport.get("triggers"):
        status_text += "\n\n## Triggered Decisions\n\n"
        for t in dreport["triggers"]:
            docs = ", ".join(t["changed_docs"])
            status_text += f"- **{t['decision']}**: grounding documents changed ({docs})\n"

    if phases:
        status_text += "\n\n## Process Availability\n\n"
        for p in phases:
            status_text += f"- **{p['process']}**: {p['status']}"
            if p.get("reason"):
                status_text += f" — {p['reason']}"
            status_text += "\n"

    notes_path = proto_dir / "notes.md"
    if notes_path.exists():
        notes_content = notes_path.read_text(encoding="utf-8").strip()
        if notes_content:
            status_text += f"\n\n## Notes\n\n{notes_content}"

    if action:
        status_text += (
            f"\n\n## Recommended Next Step\n\n"
            f"**{action.get('document', 'unknown')}**"
        )
        if action.get("reason"):
            status_text += f": {action['reason']}"
        if action.get("process"):
            guide_content = _guide_text(action["process"])
            if guide_content is not None:
                status_text += (
                    f"\n\n---\n\n"
                    f"## Process Guide: {action['process']}\n\n"
                    f"{guide_content}"
                )
            else:
                status_text += (
                    f"\n\nProcess: {action['process']}"
                )

    return status_text


def check_decision(
    description: str,
    project_dir: str | None = None,
) -> str:
    """Check whether a proposed change conflicts with existing decisions or requirements.

    Call this BEFORE making choices that would be expensive to reverse:
    new services, auth/trust models, data schemas, external integrations,
    significant API contracts. Returns any relevant existing decisions and
    requirements so you can check for conflicts before proceeding.

    Args:
        description: What you plan to do or change.
        project_dir: Project directory (default: CLAUDE_PROJECT_DIR or cwd).
    """
    proto_dir = _resolve_protocol_dir(project_dir)
    if not proto_dir.exists():
        return "No protocol directory found. No existing decisions to check against."

    from protocol_status import is_template

    sections: list[str] = []

    decisions_dir = proto_dir / "decisions"
    if decisions_dir.exists():
        decision_files = sorted(decisions_dir.glob("decision-*.md"))
        if decision_files:
            sections.append("## Existing Decisions\n")
            for df in decision_files:
                content = df.read_text(encoding="utf-8")
                sections.append(f"### {df.stem}\n\n{content}\n")

    req_path = proto_dir / "goal" / "requirements.md"
    if req_path.exists():
        if not is_template(req_path):
            content = req_path.read_text(encoding="utf-8")
            sections.append(f"## Current Requirements\n\n{content}\n")

    arch_path = proto_dir / "solution" / "architecture.md"
    if arch_path.exists():
        if not is_template(arch_path):
            content = arch_path.read_text(encoding="utf-8")
            sections.append(f"## Current Architecture\n\n{content}\n")

    if not sections:
        return (
            "No decisions, requirements, or architecture documents found. "
            "Proceed, but consider recording this as a decision with "
            "record_decision if it is significant."
        )

    header = (
        f"## Proposed Change\n\n{description}\n\n"
        "Review the following existing context for conflicts "
        "before proceeding.\n\n"
    )
    return header + "\n".join(sections)


def get_packet_status(
    project_dir: str | None = None,
    output_format: str = "agent",
) -> str:
    """Check the status of all protocol documents: staleness, dependencies,
    what needs updating.

    Call this after completing significant implementation work (new features,
    architectural changes) to see if protocol documents need updating.
    Returns a structured report showing which documents are current,
    stale, empty, or untracked.
    """
    from protocol_status import (
        check_packet_status as _check,
    )
    from protocol_status import (
        format_for_agent,
        format_report,
    )

    proto_dir = _resolve_protocol_dir(project_dir)
    if not proto_dir.exists():
        return "No protocol directory found."

    report = _check(proto_dir)
    if output_format == "human":
        return format_report(report, verbose=True)
    elif output_format == "json":
        return json.dumps(report, indent=2, default=str)
    else:
        return format_for_agent(report)


def read_protocol_document(
    document_path: str,
    project_dir: str | None = None,
) -> str:
    """Read a document from the project's .clarity-protocol/ directory.

    Use forward slashes for nested paths (e.g., 'goal/problem.md').
    """
    proto_dir = _resolve_protocol_dir(project_dir)
    file_path = (proto_dir / document_path).resolve()

    if not file_path.is_relative_to(proto_dir.resolve()):
        return "Error: path traversal not allowed."
    if not file_path.exists():
        return f"Error: document not found: {document_path}"

    return file_path.read_text(encoding="utf-8")


def write_protocol_document(
    document_path: str,
    content: str,
    project_dir: str | None = None,
) -> str:
    """Write or update a document in the project's .clarity-protocol/ directory.

    Automatically records the content hash so the staleness tracker
    knows the document is current.
    """
    proto_dir = _resolve_protocol_dir(project_dir)
    file_path = (proto_dir / document_path).resolve()

    if not file_path.is_relative_to(proto_dir.resolve()):
        return "Error: path traversal not allowed."

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    try:
        from protocol_status import record_hashes
        record_hashes(proto_dir, [document_path])
    except Exception:
        pass

    return f"Written: {document_path}"


def record_decision(
    title: str,
    context: str,
    decision: str,
    rationale: str,
    alternatives: str = "",
    consequences: str = "",
    related_docs: list[str] | None = None,
    project_dir: str | None = None,
) -> str:
    """Record a project decision with structured analysis.

    Call this after making a significant architectural or design choice
    to create a permanent record. Creates a decision document in the
    protocol's decisions/ directory.
    """
    from protocol_status import (
        record_decision as _record_decision,
    )
    from protocol_status import (
        write_decision_file,
    )

    proto_dir = _resolve_protocol_dir(project_dir)

    content_parts: list[str] = [
        f"# Decision: {title}\n",
        "**Status:** decided\n",
        f"**Date:** {datetime.now(UTC).strftime('%Y-%m-%d')}\n",
        f"\n## Context\n\n{context}\n",
        f"\n## Decision\n\n{decision}\n",
        f"\n## Rationale\n\n{rationale}\n",
    ]
    if alternatives:
        content_parts.append(f"\n## Alternatives Considered\n\n{alternatives}\n")
    if consequences:
        content_parts.append(f"\n## Consequences\n\n{consequences}\n")

    content = "\n".join(content_parts)

    filename, _ = write_decision_file(proto_dir, title, content)

    # Track under the full file stem (upstream extracts only the number
    # prefix, which diverges from the guide CLI's `decision-XX-name` ids
    # and double-records when both paths run; R17 deviation).
    decision_id = Path(filename).stem

    try:
        _record_decision(
            proto_dir,
            decision_id=decision_id,
            status="decided",
            related_docs=related_docs,
        )
    except Exception as exc:
        return f"Recorded decision: {title} → decisions/{filename} (warning: status tracking failed: {exc})"

    return f"Recorded decision: {title} → decisions/{filename}"


def record_failure(
    title: str,
    description: str,
    additional_context: str = "",
    pre_existing: bool | None = None,
    source: str = "mcp",
    project_dir: str | None = None,
) -> str:
    """Record a potential failure mode during brainstorming.

    Call this during failure brainstorming sessions when you identify
    a way the system could fail. Writes to the failure-brainstorm
    mailbox in the protocol directory.
    """
    from brainstorm import record_failure as _record

    proto_dir = _resolve_protocol_dir(project_dir)
    _, msg = _record(
        proto_dir,
        title=title,
        description=description,
        source=source,
        additional_context=additional_context,
        pre_existing=pre_existing,
    )
    return msg


def record_suggestion(
    title: str,
    target_document: str,
    suggestion: str,
    rationale: str = "",
    source: str = "mcp",
    project_dir: str | None = None,
) -> str:
    """Record a suggestion to update a project document.

    Writes to the suggestions mailbox so the suggestion can be
    reviewed and applied later.
    """
    from suggestion import (
        record_suggestion as _record,
    )

    proto_dir = _resolve_protocol_dir(project_dir)
    _, msg = _record(
        proto_dir,
        title=title,
        target_document=target_document,
        suggestion=suggestion,
        source=source,
        rationale=rationale,
    )
    return msg


# ===================================================================
# MCP RESOURCES
# ===================================================================

_CLAUDITY_BLOCK_RE = re.compile(
    r"<!-- claudity-begin -->.*?<!-- claudity-end -->", re.DOTALL
)


def project_summary() -> str:
    """Read the project summary from .clarity-protocol/summary.md."""
    proto_dir = _resolve_protocol_dir()
    summary_path = proto_dir / "summary.md"
    if not summary_path.exists():
        return "No project summary found."
    return summary_path.read_text(encoding="utf-8")


def decisions_resource() -> str:
    """Read all project decision records concatenated into one document."""
    proto_dir = _resolve_protocol_dir()
    decisions_dir = proto_dir / "decisions"
    if not decisions_dir.exists():
        return "No decisions directory found."

    parts: list[str] = []
    for df in sorted(decisions_dir.glob("decision-*.md")):
        parts.append(df.read_text(encoding="utf-8"))

    if not parts:
        return "No decision records found."
    return "\n\n---\n\n".join(parts)


def behaviors_resource() -> str:
    """Read the cross-cutting behavioral guidelines.

    Claudity reads the ``<!-- claudity-begin -->`` block from the
    project's CLAUDE.md (installed by /claudity:embed). Upstream reads
    the clarity block from AGENTS.md and refreshes it first via
    ``ensure_for_project``; resource reads here are side-effect-free.
    """
    claude_md = _resolve_project_dir() / "CLAUDE.md"
    if not claude_md.exists():
        return (
            "CLAUDE.md not found in this project. Run /claudity:embed "
            "to create it."
        )
    match = _CLAUDITY_BLOCK_RE.search(claude_md.read_text(encoding="utf-8"))
    if match is None:
        return (
            "CLAUDE.md exists but has no Claudity block (no "
            "<!-- claudity-begin --> / <!-- claudity-end --> markers). "
            "Re-run /claudity:embed to refresh it."
        )
    return match.group(0)


def process_guide_resource(name: str) -> str:
    """Read a process guide by name."""
    text = _guide_text(name)
    if text is None:
        return f"Process guide not found: {name}"
    return text


def thinker_guide_resource(name: str) -> str:
    """Read a thinker guide by name.

    Served from the plugin's agents/ directory with the Claude Code
    frontmatter stripped (R16 packaging, not methodology).
    """
    guide_path = _resolve_agent_dir() / "agents" / f"{name}.md"
    if not guide_path.exists():
        return f"Thinker guide not found: {name}"
    return _FRONTMATTER_RE.sub("", guide_path.read_text(encoding="utf-8"), count=1)


def protocol_document_resource(path: str) -> str:
    """Read any protocol document by path.

    Use forward slashes for nested paths (e.g., 'goal/problem.md').
    """
    proto_dir = _resolve_protocol_dir()
    file_path = (proto_dir / path).resolve()
    if not file_path.is_relative_to(proto_dir.resolve()):
        return "Error: path traversal not allowed."
    if not file_path.exists():
        return f"Document not found: {path}"
    return file_path.read_text(encoding="utf-8")


RESOURCES: list[dict] = [
    {
        "uri": "clarity://summary",
        "name": "project_summary",
        "description": "The project summary (.clarity-protocol/summary.md).",
        "fn": project_summary,
    },
    {
        "uri": "clarity://decisions",
        "name": "decisions_resource",
        "description": "All project decision records, concatenated.",
        "fn": decisions_resource,
    },
    {
        "uri": "clarity://behaviors",
        "name": "behaviors_resource",
        "description": "The cross-cutting behavioral guidelines (the Claudity block in CLAUDE.md).",
        "fn": behaviors_resource,
    },
]

RESOURCE_TEMPLATES: list[dict] = [
    {
        "uriTemplate": "clarity://processes/{name}",
        "name": "process_guide_resource",
        "description": "A clarity process guide by name (e.g. failure-analysis).",
        "prefix": "clarity://processes/",
        "fn": process_guide_resource,
    },
    {
        "uriTemplate": "clarity://thinkers/{name}",
        "name": "thinker_guide_resource",
        "description": "A specialist thinker's methodology guide by name.",
        "prefix": "clarity://thinkers/",
        "fn": thinker_guide_resource,
    },
    {
        "uriTemplate": "clarity://protocol/{path}",
        "name": "protocol_document_resource",
        "description": "Any protocol document by path (e.g. goal/problem.md).",
        "prefix": "clarity://protocol/",
        "fn": protocol_document_resource,
    },
]

_RESOURCE_INDEX = {r["uri"]: r for r in RESOURCES}


def _read_resource(uri: str) -> str | None:
    """Resolve a resource URI to its text, or None if no route matches."""
    concrete = _RESOURCE_INDEX.get(uri)
    if concrete is not None:
        return concrete["fn"]()
    for template in RESOURCE_TEMPLATES:
        if uri.startswith(template["prefix"]):
            arg = uri[len(template["prefix"]):]
            if arg:
                return template["fn"](arg)
    return None


# ===================================================================
# Stdlib MCP stdio transport (replaces FastMCP per PORTING.md R17)
# ===================================================================

SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

_PROJECT_DIR_PROP = {
    "type": "string",
    "description": "Project directory (default: CLAUDE_PROJECT_DIR or cwd).",
}


def _schema(properties: dict, required: list[str]) -> dict:
    props = dict(properties)
    props["project_dir"] = _PROJECT_DIR_PROP
    return {"type": "object", "properties": props, "required": required}


TOOLS: list[dict] = [
    {
        "name": "run_clarity",
        "fn": run_clarity,
        "inputSchema": _schema({}, []),
    },
    {
        "name": "check_decision",
        "fn": check_decision,
        "inputSchema": _schema(
            {"description": {"type": "string", "description": "What you plan to do or change."}},
            ["description"],
        ),
    },
    {
        "name": "get_packet_status",
        "fn": get_packet_status,
        "inputSchema": _schema(
            {
                "output_format": {
                    "type": "string",
                    "enum": ["agent", "human", "json"],
                    "description": "Report format (default: agent).",
                }
            },
            [],
        ),
    },
    {
        "name": "read_protocol_document",
        "fn": read_protocol_document,
        "inputSchema": _schema(
            {
                "document_path": {
                    "type": "string",
                    "description": "Document path relative to the protocol directory (e.g. 'goal/problem.md').",
                }
            },
            ["document_path"],
        ),
    },
    {
        "name": "write_protocol_document",
        "fn": write_protocol_document,
        "inputSchema": _schema(
            {
                "document_path": {
                    "type": "string",
                    "description": "Document path relative to the protocol directory (e.g. 'goal/problem.md').",
                },
                "content": {"type": "string", "description": "Full markdown content to write."},
            },
            ["document_path", "content"],
        ),
    },
    {
        "name": "record_decision",
        "fn": record_decision,
        "inputSchema": _schema(
            {
                "title": {"type": "string", "description": "Short decision title."},
                "context": {"type": "string", "description": "The situation that forced the decision."},
                "decision": {"type": "string", "description": "What was decided."},
                "rationale": {"type": "string", "description": "Why this option won."},
                "alternatives": {"type": "string", "description": "Optional: alternatives considered."},
                "consequences": {"type": "string", "description": "Optional: consequences of the decision."},
                "related_docs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Protocol documents whose content grounded this decision, relative to the protocol directory (e.g. ['solution/solution.md', 'goal/requirements.md']). Always pass the documents you consulted: if any of them change later, the decision is flagged for reconsideration — without them it never will be.",
                },
            },
            ["title", "context", "decision", "rationale"],
        ),
    },
    {
        "name": "record_failure",
        "fn": record_failure,
        "inputSchema": _schema(
            {
                "title": {"type": "string", "description": "Short descriptive title of what could go wrong."},
                "description": {
                    "type": "string",
                    "description": "1-3 sentences: what goes wrong, how it happens, and who is harmed. Must end in actual harm.",
                },
                "additional_context": {
                    "type": "string",
                    "description": "Optional: more detail about severity, related concerns, initial thoughts on the failure chain.",
                },
                "pre_existing": {
                    "type": "boolean",
                    "description": "Optional: true if this failure also exists (at similar or greater severity) in the world before this solution is implemented.",
                },
                "source": {
                    "type": "string",
                    "description": "Optional: where this failure came from — a thinker name, 'human (<name or role>)' for user contributions, or omitted for your own analysis.",
                },
            },
            ["title", "description"],
        ),
    },
    {
        "name": "record_suggestion",
        "fn": record_suggestion,
        "inputSchema": _schema(
            {
                "title": {"type": "string", "description": "Short descriptive title for the suggestion."},
                "target_document": {
                    "type": "string",
                    "description": "The document to update, relative to the protocol directory (e.g. 'goal/stakeholders.md').",
                },
                "suggestion": {"type": "string", "description": "The suggested content to add or change."},
                "rationale": {"type": "string", "description": "Optional: why this update is needed."},
                "source": {
                    "type": "string",
                    "description": "Optional: where this suggestion came from — a thinker name, or omitted for your own analysis.",
                },
            },
            ["title", "target_document", "suggestion"],
        ),
    },
]

_TOOL_INDEX = {t["name"]: t for t in TOOLS}


def _tool_listing() -> list[dict]:
    """tools/list payload: schemas plus docstring-derived descriptions."""
    return [
        {
            "name": t["name"],
            "description": (t["fn"].__doc__ or "").strip(),
            "inputSchema": t["inputSchema"],
        }
        for t in TOOLS
    ]


def _rpc_result(req_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _rpc_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_result(text: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _handle_tools_call(req_id, params: dict) -> dict:
    name = params.get("name")
    tool = _TOOL_INDEX.get(name)
    if tool is None:
        return _rpc_error(req_id, -32602, f"Unknown tool: {name}")

    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _rpc_error(req_id, -32602, "tool arguments must be an object")

    missing = [k for k in tool["inputSchema"]["required"] if k not in arguments]
    if missing:
        return _rpc_result(
            req_id,
            _tool_result(f"Error: missing required argument(s): {', '.join(missing)}", True),
        )

    allowed = set(tool["inputSchema"]["properties"])
    kwargs = {k: v for k, v in arguments.items() if k in allowed}

    try:
        out = tool["fn"](**kwargs)
    except Exception as exc:  # tool errors are results, not protocol errors
        return _rpc_result(req_id, _tool_result(f"Error: {exc}", True))
    return _rpc_result(req_id, _tool_result(out))


def _handle(req: dict) -> dict | None:
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        client_version = params.get("protocolVersion", "")
        version = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else "2025-06-18"
        return _rpc_result(req_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": SERVER_NAME, "version": _server_version()},
            "instructions": SERVER_INSTRUCTIONS,
        })
    if method == "ping":
        return _rpc_result(req_id, {})
    if method == "tools/list":
        return _rpc_result(req_id, {"tools": _tool_listing()})
    if method == "tools/call":
        return _handle_tools_call(req_id, params)
    if method == "resources/list":
        return _rpc_result(req_id, {"resources": [
            {"uri": r["uri"], "name": r["name"], "description": r["description"],
             "mimeType": "text/markdown"}
            for r in RESOURCES
        ]})
    if method == "resources/templates/list":
        return _rpc_result(req_id, {"resourceTemplates": [
            {"uriTemplate": t["uriTemplate"], "name": t["name"],
             "description": t["description"], "mimeType": "text/markdown"}
            for t in RESOURCE_TEMPLATES
        ]})
    if method == "resources/read":
        uri = params.get("uri", "")
        try:
            text = _read_resource(uri)
        except Exception as exc:  # noqa: BLE001 — surface as protocol error
            return _rpc_error(req_id, -32603, f"Resource read failed: {exc}")
        if text is None:
            return _rpc_error(req_id, -32002, f"Resource not found: {uri}")
        return _rpc_result(req_id, {"contents": [
            {"uri": uri, "mimeType": "text/markdown", "text": text}
        ]})
    return _rpc_error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    """Newline-delimited JSON-RPC over stdio.

    stdout carries protocol messages exclusively; diagnostics go to
    stderr. Notifications (messages without an id) are consumed silently.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        if "id" not in req:
            continue
        resp = _handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
