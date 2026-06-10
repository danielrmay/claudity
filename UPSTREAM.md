# Upstream tracking

*For contributors and maintainers. Users of the plugin don't need anything here.*

Vendored from [microsoft/clarity-agent](https://github.com/microsoft/clarity-agent)
at commit `6b32c4349502d56d1c2e863c4778b322f8ff9466` (main, fetched 2026-06-09;
upstream release v0.1.2).

**[`upstream.json`](upstream.json) is the machine-readable source of truth**
for the pin and the vendored-path watch list. CI enforces that every vendored
file's header matches its pin and that this file and NOTICE.md carry it. The
table below is commentary on the same mapping.

## Vendoring map

| Upstream path | Claudity path | Fidelity |
|---|---|---|
| `processes/clarity-agent.md` | `skills/start/reference/clarity-agent.upstream.md` | verbatim (reference only, not executed) |
| `processes/clarity-agent.md` | `skills/start/SKILL.md` + `skills/start/reference/routing.md` | rewritten as the router skill |
| `processes/problem-clarification.md` | `skills/start/processes/problem-clarification.md` | near-verbatim + PORTING rules |
| `processes/decision-guidance.md` | `skills/decide/SKILL.md` | near-verbatim + PORTING rules (packaged as a skill, R16) |
| `processes/solution-brainstorming.md` | `skills/start/processes/solution-brainstorming.md` | near-verbatim + PORTING rules |
| `processes/architecture-design.md` | `skills/start/processes/architecture-design.md` | near-verbatim + PORTING rules |
| `processes/discovery-research.md` | `skills/start/processes/discovery-research.md` | near-verbatim + PORTING rules |
| `processes/discovery-prototype.md` | `skills/start/processes/discovery-prototype.md` | near-verbatim + PORTING rules |
| `processes/message-clarification.md` | `skills/message/SKILL.md` | near-verbatim + PORTING rules (packaged as a skill, R16) |
| `processes/failure-brainstorming.md` | `skills/risks/SKILL.md` | adapted (mailbox → parallel subagents, R9/R14; packaged as a skill, R16) |
| `processes/failure-analysis.md` | `skills/start/processes/failure-analysis.md` | near-verbatim + PORTING rules |
| `processes/failure-management.md` | `skills/start/processes/failure-management.md` | near-verbatim + PORTING rules |
| `processes/failure-reasoning-guidelines.md` | `skills/start/processes/failure-reasoning-guidelines.md` | verbatim |
| `thinkers/*.md` (6 files) | `agents/*.md` | body near-verbatim; frontmatter converted to Claude Code agent format, upstream metadata moved to a body section |
| `src/clarity_agent/setup/snippet.md` | `skills/embed/SKILL.md` | adapted for CLAUDE.md / no MCP server; inlined as the embed skill's template section (R16) |
| `src/clarity_agent/protocol/packet_status.py` | `scripts/protocol_status.py` | whole file; package imports inlined (see its docstring) |
| `src/clarity_agent/protocol/initialize.py` | `scripts/protocol_init.py` | adapted (see its docstring); templates verbatim |
| `catalogs/security-catalog.csv` | `catalogs/security-catalog.csv` | verbatim |
| `tests/test_packet_status.py` | `tests/test_protocol_status.py` | adapted imports + Mailbox stub (see its docstring) |
| `tests/conftest.py` | `tests/conftest.py` | fixtures only, keyring/Settings dropped |
| `LICENSE` | `NOTICE.md` (quoted) | verbatim |

## Sync policy

**In scope** (the `upstream.json` watch set): process guides, thinkers, the
security catalog, the protocol scripts (`packet_status.py`, `initialize.py`),
the agent snippet, the packet-status tests, and the license. New upstream
files appearing under `processes/`, `thinkers/`, or `catalogs/` are surfaced
by the watcher as adoption candidates; once adopted they join the watch set.

**Out of scope, never ported:** the agent harness — web UI, Tauri desktop
app, LLM backends, MCP server, evals framework, transcript system,
installers, dev-tools, and the VS Code extension. Claudity replaces these
with Claude Code natives. CI's harness-residue lints
(`tests/test_plugin_structure.py`) guard against accidental bleed-through.

**Cadence:** the `upstream-watch` workflow runs nightly (02:43 UTC) and on
demand via `workflow_dispatch`. When upstream changes touch the watch set it
opens or refreshes a single issue labeled `upstream-sync`. Re-syncs are
batched per issue, not per upstream commit; upstream releases every 2-3
weeks, so most issues will accumulate toward one upstream release.

**Accepting changes:** for each changed file in the issue, follow the
re-sync procedure below. Adaptations must trace to a PORTING.md rule; a
change that needs a new kind of substitution gets a new numbered rule first.
After re-applying, bump the pin in `upstream.json` and the vendored file
headers (CI fails until they agree), update NOTICE.md and this file, run
Tier 1 and Tier 2 tests, and record the new pin in the CHANGELOG entry.

## Versioning and releases

Claudity uses independent semver (0.x until the full process surface has been
exercised on real projects end to end):

- **PATCH** — local fixes, docs, test changes; no guide-behavior change
- **MINOR** — upstream re-syncs that change guide content/behavior, new
  thinkers or commands, new features
- **MAJOR** — breaking changes to the protocol directory format or the
  command surface

Release steps: bump `version` in `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` (a test enforces they agree; packets record
the version via `protocol_init.py`), move the Unreleased CHANGELOG section to
the new version with the upstream pin it tracks, then run
`claude plugin tag` (creates a validated `claudity--vX.Y.Z` git tag) and push
the tag.

## Fidelity audit

`python3 scripts/upstream_audit.py` (runs in CI) is the confidence check for
the verbatim claim: it fetches the pinned upstream text for every watch
entry, strips Claudity packaging (frontmatter, vendor header, R16 preamble;
the embed skill's fenced snippet template is extracted), and classifies every
remaining changed line against patterns keyed to PORTING.md rule IDs.
Unexplained lines fail the build. Verbatim entries (the security catalog, the
upstream router reference copy) must be byte-identical; entries marked
`"fidelity": "adapted"` in upstream.json (failure-brainstorming) and the
Python/test files are reported informationally — their contracts are their
header notes and docstrings.

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
5. For R16-packaged units (the decide/risks/message skills, the thinkers,
   the embed snippet), re-apply the new upstream text below the frontmatter,
   vendor header, and preamble — the packaging stays, the vendored body
   changes.
6. Run `.venv/bin/pytest tests/ -q` and `python3 scripts/upstream_audit.py`
   (extend its allowlist only for changes that trace to a rule), run the M1
   staleness round-trip (see README), update the pinned SHA in
   `upstream.json`, here, in NOTICE.md, and in the vendored file headers
   (the pin-consistency tests fail until all agree).
