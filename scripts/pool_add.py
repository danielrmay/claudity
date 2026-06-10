#!/usr/bin/env python3
"""
Write raw failures into the brainstorming pool, one file per failure.

Replaces upstream clarity-agent's `record_failure` tool for the same reason
upstream made it a tool: models are unreliable at file-layout bookkeeping.
This script owns placement (always the pool top level), naming
(``<source>--<slug>.md``), and format, deterministically.

Usage:
  # Persist a thinker's structured output (its '## Failures' section):
  python3 pool_add.py <project_dir> <source> --file thinker-output.md
  python3 pool_add.py <project_dir> <source> < thinker-output.md

  # Record a single failure:
  python3 pool_add.py <project_dir> <source> --title "What goes wrong" < description.txt

<source> is e.g. ``general-thinker``, ``broad-analysis``, or ``human``.
Prints one line per pool file written. Exits 2 if no failures were found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PROTOCOL_DIR_DOT = ".clarity-protocol"
_PROTOCOL_DIR_VISIBLE = "Clarity Protocol"


def _resolve_protocol_dir(project_dir: Path) -> Path:
    dot = project_dir / _PROTOCOL_DIR_DOT
    visible = project_dir / _PROTOCOL_DIR_VISIBLE
    if dot.exists():
        return dot
    if visible.exists():
        return visible
    if (project_dir / ".git").exists():
        return dot
    return visible


def _slug(title: str, max_length: int = 50) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:max_length] or "failure"


def parse_failures(text: str) -> list[tuple[str, str]]:
    """Extract (title, body) pairs from a thinker's structured output.

    Reads the '## Failures' section if present (stopping at the next '## '
    heading), else the whole text. Each '### <title>' starts a failure; its
    body runs to the next '###'.
    """
    m = re.search(r"^##\s+Failures\s*$", text, re.MULTILINE)
    if m:
        section = text[m.end():]
        nxt = re.search(r"^##\s+\S", section, re.MULTILINE)
        if nxt:
            section = section[: nxt.start()]
    else:
        section = text

    failures: list[tuple[str, str]] = []
    parts = re.split(r"^###\s+", section, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if title:
            failures.append((title, body))
    return failures


def write_failure(pool: Path, source: str, title: str, body: str) -> Path:
    name = f"{source}--{_slug(title)}"
    path = pool / f"{name}.md"
    counter = 2
    while path.exists():
        path = pool / f"{name}-{counter}.md"
        counter += 1

    content = f"# {title}\n\n- **Source:** {source}\n"
    if body:
        content += f"\n{body}\n"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write raw failures into the brainstorming pool, one file per failure",
    )
    parser.add_argument("project_dir", help="Project directory containing the protocol dir")
    parser.add_argument("source", help="Attribution, e.g. general-thinker, broad-analysis, human")
    parser.add_argument("--file", help="Read input from this file instead of stdin")
    parser.add_argument("--title", help="Record a single failure with this title (input = description)")
    args = parser.parse_args()

    protocol_dir = _resolve_protocol_dir(Path(args.project_dir))
    if not protocol_dir.exists():
        parser.error(f"No protocol directory found in {args.project_dir}")
    pool = protocol_dir / "failures" / "pool"
    pool.mkdir(parents=True, exist_ok=True)

    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()

    if args.title:
        failures = [(args.title, text.strip())]
    else:
        failures = parse_failures(text)

    if not failures:
        print(
            "No failures found: expected '### <title>' blocks "
            "(under a '## Failures' heading), or use --title for a single failure.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    for title, body in failures:
        print(write_failure(pool, args.source, title, body))


if __name__ == "__main__":
    main()
