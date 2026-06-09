# Upstream tracking

Vendored from [microsoft/clarity-agent](https://github.com/microsoft/clarity-agent)
at commit `6b32c4349502d56d1c2e863c4778b322f8ff9466` (main, fetched 2026-06-09).

## Vendoring map

| Upstream path | Claudity path | Fidelity |
|---|---|---|
| `processes/clarity-agent.md` | `skills/claudity/reference/clarity-agent.upstream.md` | verbatim (reference only, not executed) |
| `processes/clarity-agent.md` | `skills/claudity/SKILL.md` + `skills/claudity/reference/routing.md` | rewritten as the router skill |
| `processes/problem-clarification.md` | `skills/claudity/processes/problem-clarification.md` | near-verbatim + PORTING rules |
| `processes/decision-guidance.md` | `skills/claudity/processes/decision-guidance.md` | near-verbatim + PORTING rules |
| `processes/solution-brainstorming.md` | `skills/claudity/processes/solution-brainstorming.md` | near-verbatim + PORTING rules |
| `processes/architecture-design.md` | `skills/claudity/processes/architecture-design.md` | near-verbatim + PORTING rules |
| `processes/discovery-research.md` | `skills/claudity/processes/discovery-research.md` | near-verbatim + PORTING rules |
| `processes/discovery-prototype.md` | `skills/claudity/processes/discovery-prototype.md` | near-verbatim + PORTING rules |
| `processes/message-clarification.md` | `skills/claudity/processes/message-clarification.md` | near-verbatim + PORTING rules |
| `processes/failure-brainstorming.md` | `skills/claudity/processes/failure-brainstorming.md` | adapted (mailbox → parallel subagents, R9/R14) |
| `processes/failure-analysis.md` | `skills/claudity/processes/failure-analysis.md` | near-verbatim + PORTING rules |
| `processes/failure-management.md` | `skills/claudity/processes/failure-management.md` | near-verbatim + PORTING rules |
| `processes/failure-reasoning-guidelines.md` | `skills/claudity/processes/failure-reasoning-guidelines.md` | verbatim |
| `thinkers/*.md` (6 files) | `agents/*.md` | body near-verbatim; frontmatter converted to Claude Code agent format, upstream metadata moved to a body section |
| `src/clarity_agent/setup/snippet.md` | `skills/claudity/reference/snippet.md` | adapted for CLAUDE.md / no MCP server |
| `src/clarity_agent/protocol/packet_status.py` | `scripts/protocol_status.py` | whole file; package imports inlined (see its docstring) |
| `src/clarity_agent/protocol/initialize.py` | `scripts/protocol_init.py` | adapted (see its docstring); templates verbatim |
| `catalogs/security-catalog.csv` | `catalogs/security-catalog.csv` | verbatim |
| `tests/test_packet_status.py` | `tests/test_protocol_status.py` | adapted imports + Mailbox stub (see its docstring) |
| `tests/conftest.py` | `tests/conftest.py` | fixtures only, keyring/Settings dropped |
| `LICENSE` | `NOTICE.md` (quoted) | verbatim |

## Re-sync procedure

1. Pick the new upstream commit `NEW_SHA`; fetch each upstream file in the map:
   `curl -s https://raw.githubusercontent.com/microsoft/clarity-agent/NEW_SHA/<path>`.
2. For each vendored file, three-way compare: pinned upstream version vs new
   upstream version (what changed upstream) and pinned upstream version vs the
   Claudity file (our PORTING.md substitutions).
3. Re-apply the substitutions to the new upstream text. Substitutions are
   mechanical (see PORTING.md); anything that doesn't fit an existing rule
   needs a new rule, not an ad-hoc edit.
4. For `SKILL.md`/`routing.md`, diff the new `clarity-agent.md` against
   `reference/clarity-agent.upstream.md` and fold routing changes into the
   skill by hand; then update the reference copy.
5. Run `.venv/bin/pytest tests/ -q`, run the M1 staleness round-trip
   (see README), update the pinned SHA here and in NOTICE.md and the vendored
   file headers.
