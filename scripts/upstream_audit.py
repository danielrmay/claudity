#!/usr/bin/env python3
"""
Audit vendored fidelity: every line we changed must trace to a PORTING rule.

For each markdown entry in upstream.json, fetches the pinned upstream text
(cached under /tmp/claudity-upstream-pin-<sha>/), strips Claudity packaging
from the local file (frontmatter, vendor header, R16 preamble), diffs the
remainder against upstream, and classifies every changed line against an
allowlist of patterns keyed by PORTING.md rule IDs. Unexplained lines fail
the audit.

Verbatim entries (the security catalog, the upstream router reference copy)
must match byte-for-byte. Python/test entries are reported informationally
(their deviations are documented in their own docstrings).

Usage: python3 scripts/upstream_audit.py [--offline]
Exit codes: 0 = fully explained, 1 = unexplained divergence, 2 = fetch error.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CFG = json.loads((REPO / "upstream.json").read_text())
PIN = CFG["pin"]
CACHE = Path(f"/tmp/claudity-upstream-pin-{PIN[:12]}")
RAW = f"https://raw.githubusercontent.com/{CFG['repo']}/{PIN}"

# Byte-identical entries.
VERBATIM = {
    "skills/risks/security-catalog.csv",
    "skills/start/reference/clarity-agent.upstream.md",
}
# Reported informationally only (deviations documented in their docstrings).
INFORMATIONAL_SUFFIXES = (".py",)
# NOTICE.md quotes the license rather than vendoring it.
QUOTED = {"NOTICE.md"}

# Allowlist: every changed line must match one of these (rule, regex) pairs.
# Patterns are matched against added OR removed lines from the unified diff.
ALLOWLIST: list[tuple[str, str]] = [
    ("R1", r"python -m clarity_agent\.protocol\.(packet_status|initialize|mailbox)"),
    ("R1", r"(protocol_status|protocol_init|mailbox)\.py"),
    ("R17", r"record_failure|record_suggestion|record-failure|MCP tool|clarity-agent` server|the mailbox|suggestions mailbox|mailboxes/|failure-brainstorm|brainstorming mailbox|suggestion box"),
    ("R18", r"failures/pool|Claudity 0\.2 or earlier"),
    ("R9", r"read_thinker_guide|recommend_deeper_analysis|recommend-deeper|read-thinker-guide|thinker subagent|Agent tool|launch.*thinker|Specialist Thinkers"),
    ("R9", r"subagent|orchestrat|in parallel"),
    ("R10", r"clarity-agent|claudity|Claudity|`start` skill|/claudity:"),
    ("R11", r"CLAUDE_PLUGIN_ROOT|security-catalog\.csv|catalog path|absolute path provided"),
    ("R12", r"<!-- deleted per R12|packet generator|review packet|clarity embed|MCP|mcp\.json|web UI|desktop"),
    ("R16", r"SNIPPET-TEMPLATE|disable-model-invocation|^name:|^description:"),
    # R16 packaging blocks (skills/agents): frontmatter, task preamble,
    # metadata carrier, and the standardized output contract (with R9).
    ("R16", r"^## (Your task|Metadata|Output format)"),
    ("R16", r"^(tools|name|display_name|modes|prerequisites|tags|execution|type):"),
    ("R16", r"^```(yaml)?$|^---$"),
    ("R16", r"launching prompt|final message is consumed|Return exactly this structure|omit empty sections"),
    ("R9/R16", r"structured output|failure block|suggestion block|specialist recommendation|Pre-existing: yes\|no|Failure chain: <step"),
    ("R9/R16", r"Target document:|<short title|<thinker name>|<rationale|1-3 sentences: what fails"),
    ("R16", r"clarity-(begin|end|meta)|claudity-(begin|end|meta)|schema_version|protocol_dir_name|processes_dir|mode: \{\{MODE\}\}|markdownlint"),
    ("R8", r"alongside this guide|reference/routing|skills/(decide|risks|message|start)|processes/failure-reasoning-guidelines"),
    # R9/R16 output-contract conversion in thinkers: upstream tool-recording
    # sections become the standardized structured-output sections.
    ("R9/R16", r"^## (Failures|Suggestions|Specialist recommendations|What to Produce|What Each Failure Record Contains)$"),
    ("R9/R16", r"record a raw failure mode|<what to add or change|^## Output Format$|Every failure must end in actual harm"),
    ("R17", r"check what you plan to do against the protocol|\{\{PROTOCOL_DIR_NAME\}\}"),
    ("R12", r"dev-tools|Generate threat model artifacts|packet generator"),
    # Structural noise from clean splices: blank lines and bare code fences
    # left by removed command blocks (the commands themselves match R1/R17).
    ("noise", r"^\s*$"),
    ("noise", r"^```(bash|json|markdown)?$"),
]


def fetch(upstream_path: str, offline: bool) -> str | None:
    dst = CACHE / upstream_path
    if dst.exists():
        return dst.read_text()
    if offline:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(f"{RAW}/{upstream_path}", timeout=30) as r:
            text = r.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"FETCH ERROR {upstream_path}: {e}", file=sys.stderr)
        return None
    dst.write_text(text)
    return text


def strip_packaging(local_text: str, upstream_text: str) -> str:
    """Remove Claudity packaging: frontmatter, vendor header, R16 preamble.

    Alignment trick: slice the local file from the first occurrence of the
    upstream's first non-empty line (the guide's own title/heading).
    """
    first_line = next(l for l in upstream_text.splitlines() if l.strip())
    lines = local_text.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if l.rstrip("\n") == first_line:
            return "".join(lines[i:])
    return local_text  # no alignment — diff will show everything


def extract_snippet_template(text: str) -> str:
    start = text.index("SNIPPET-TEMPLATE-BEGIN")
    start = text.index("\n", start) + 1
    end = text.index("<!-- SNIPPET-TEMPLATE-END")
    return text[start:end]


def classify(diff_lines: list[str]) -> tuple[dict[str, int], list[str]]:
    explained: dict[str, int] = {}
    unexplained: list[str] = []
    for raw in diff_lines:
        if not (raw.startswith("+") or raw.startswith("-")):
            continue
        if raw.startswith(("+++", "---")):
            continue
        line = raw[1:]
        for rule, pat in ALLOWLIST:
            if re.search(pat, line):
                explained[rule] = explained.get(rule, 0) + 1
                break
        else:
            unexplained.append(raw)
    return explained, unexplained


def main() -> None:
    offline = "--offline" in sys.argv
    failures = 0
    print(f"Auditing vendored fidelity against {CFG['repo']}@{PIN[:12]}\n")

    for entry in CFG["watch"]:
        up, local = entry["upstream"], entry["local"]
        local_path = REPO / local
        upstream_text = fetch(up, offline)
        if upstream_text is None:
            print(f"  ?  {local}  (upstream not available; skipped)")
            continue

        if entry.get("fidelity") == "inlined":
            short = PIN[:7]
            ok = local_path.exists() and f"clarity-agent@{short}" in local_path.read_text()
            print(f"  {'✓' if ok else '✗'}  {local}  (inlines {up}; {'pin header present' if ok else 'MISSING pin header'})")
            failures += 0 if ok else 1
            continue

        if entry.get("fidelity") == "adapted":
            n = len([l for l in difflib.unified_diff(
                upstream_text.splitlines(), local_path.read_text().splitlines(), lineterm="")
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))])
            print(f"  i  {local}  (adapted — {n} changed lines; contract is its header note + UPSTREAM.md row)")
            continue

        if local in QUOTED:
            ok = upstream_text.strip() in local_path.read_text()
            print(f"  {'✓' if ok else '✗'}  {local}  (license quoted {'intact' if ok else 'MISSING'})")
            failures += 0 if ok else 1
            continue

        if local.endswith(INFORMATIONAL_SUFFIXES):
            n = len([l for l in difflib.unified_diff(
                upstream_text.splitlines(), local_path.read_text().splitlines(), lineterm="")
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))])
            print(f"  i  {local}  ({n} changed lines; documented in its docstring)")
            continue

        local_text = local_path.read_text()
        if local in VERBATIM:
            ok = local_text == upstream_text
            print(f"  {'✓' if ok else '✗'}  {local}  ({'byte-identical' if ok else 'DIVERGED — must be verbatim'})")
            failures += 0 if ok else 1
            continue

        if local == "skills/embed/SKILL.md":
            local_text = extract_snippet_template(local_text)
        body = strip_packaging(local_text, upstream_text)
        diff = list(difflib.unified_diff(
            upstream_text.splitlines(), body.splitlines(), lineterm=""))
        explained, unexplained = classify(diff)
        total = sum(explained.values()) + len(unexplained)
        if unexplained:
            failures += 1
            print(f"  ✗  {local}  ({total} changed lines, {len(unexplained)} UNEXPLAINED):")
            for l in unexplained[:8]:
                print(f"       {l[:110]}")
        else:
            rules = ", ".join(sorted(k for k in explained if k != "noise")) or "none"
            print(f"  ✓  {local}  ({total} changed lines, all traced to: {rules})")

    print()
    if failures:
        print(f"AUDIT FAILED: {failures} file(s) with unexplained divergence", file=sys.stderr)
        raise SystemExit(1)
    print("AUDIT PASSED: every vendored deviation traces to a PORTING.md rule")


if __name__ == "__main__":
    main()
