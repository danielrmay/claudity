# Testing

*For contributors and maintainers. Users of the plugin don't need anything here.*

The harness is tiered so inference is paid for only where behavior is
model-driven. Tiers 0 and 1 are free and run in CI on every push; Tier 2 is a
small headless smoke suite with a hard cost budget, run locally on demand.

| Tier | What | Cost | When |
| ---- | ---- | ---- | ---- |
| 0 | `claude plugin validate .` + component inventory (`claude --plugin-dir . plugin details claudity`) | free | CI, every push |
| 1 | `pytest tests/` — 71 vendored status-engine tests + structural tests (manifests, frontmatter, cross-reference integrity, porting lints, init↔staleness coupling) | free | CI, every push |
| 2 | `tests/e2e/run.sh` — 10 headless scenarios with deterministic artifact assertions | ~$2.50 (mixed Haiku/Sonnet floors) | locally, before a release or after touching SKILL.md / processes / commands / agents |

## Tier 1

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/pytest tests/ -q
```

`tests/test_plugin_structure.py` guards the load-bearing invariants:
every plugin-root path referenced in the markdown exists; the SKILL.md
process map, the `processes/` directory, the thinker table, the `agents/`
directory, and the status script's process names all agree; vendored files
carry their upstream headers with no harness residue; and a freshly
initialized packet reads as all-"empty" (the template-marker coupling).
Tests that shell out to `claude` are skipped when the CLI isn't on PATH.

## Tier 2

```bash
tests/e2e/run.sh                  # all scenarios, sequential
tests/e2e/run.sh 01               # one scenario by prefix
tests/e2e/run.sh --parallel       # all scenarios concurrently
tests/e2e/run.sh --stress 07 6    # 6 parallel copies of one scenario; pass rate
```

A scenario is a **scripted persona conversation** plus deterministic
assertions. Each `turns/NN.md` is a verbatim-plausible user message (a slash
command, an answer, an explicit acceptance) played into one headless session
(`claude -p`, then `claude -p --resume`) in a throwaway project with the
plugin loaded via `--plugin-dir`. There are no stage directions for the model
to interpret — acceptance is a real user turn, which is what makes the
record-on-acceptance rule honestly testable. Asserts check **artifacts**
(files created, `config.json` state, status-script output), never LLM-judged
transcripts; where an answer must be checked (02-routing), the oracle is
computed from the status engine's own output rather than hardcoded.

The nondeterminism stance, explicitly: the **user side is pinned** by the
script, the **model side is deliberately free** (its interpretation of the
process guides is the thing under test), and the **oracle is deterministic**.
Scenario openers must enter through real product surfaces (a `/claudity:*`
command, or natural language that engages the skill in a project carrying the
embedded CLAUDE.md snippet — the fixture includes one, as every real embedded
project does). Transcript forensics earlier showed why: sessions that never
found a guide improvised plausible-but-wrong bookkeeping instead of stopping,
and slipped past asserts that didn't check recording.

A per-scenario cost table is printed from the CLI's `total_cost_usd`; the
suite fails if a sequential run's total exceeds the budget.

| Scenario | Verifies |
| -------- | -------- |
| 01-embed | `/claudity:embed` scaffolds the packet (9 empty docs) and installs the CLAUDE.md snippet with markers and no unexpanded placeholders |
| 02-routing | `/claudity:status` runs the status script and correctly relays the recommended next process for a fixture packet |
| 03-decide | `/claudity:decide` produces a real decision document, updates the index, and records `decisionState` (status `decided`, non-empty `relatedDocs`) |
| 04-thinker | failure-brainstorming launches the `general-thinker` subagent and records its findings into `mailboxes/failure-brainstorm/` via `record_failure`, flipping the status engine to recommend `failure-analysis` |
| 05-solution | solution-brainstorming fills a blanked `solution.md` + `solution-summary.md` with real content and records them as current |
| 06-architecture | architecture-design writes `architecture.md` with the Mermaid threat-model block plus a valid `system-design.json`, and records state |
| 07-analysis | failure-analysis snapshots seeded mailbox items to `archive/failure-brainstorm/snapshot-*/`, produces analyzed `failure-NN` documents and a real index, and records state |
| 08-management | failure-management replaces a seeded placeholder `## Management Plan` with a real plan; the status engine stops recommending the phase |
| 09-message | message-clarification writes a non-template general-audience `summary.md` and records it |
| 10-record | the headless MCP canary: an ambient risk report lands as exactly one `mailboxes/failure-brainstorm/` item via the `record_failure` tool |

When iterating on `scripts/mcp_server.py`, remember MCP servers spawn at
session start — interactive sessions need a restart (or `/reload-plugins`) to
pick up server edits; `tests/test_mcp_protocol.py` drives a fresh process per
test, so pytest always sees the current code.

Discovery (`discovery-research` / `discovery-prototype`) remains uncovered:
their outputs are investigation programs and disposable prototypes with no
cheap deterministic artifact contract.

**Model floors.** Command-anchored scenarios (01, 02, 04, 09, 10) run on
Haiku — the cheapest and most demanding test of those surfaces. Ambient
skill-driven conversational scenarios (05–08) set `MODEL_FLOOR="sonnet"` in
their `config.sh`: measured on this suite, natural-language openers drove the
full pipeline reliably on Sonnet (4/4 stress on 07) but degraded on Haiku
(2/6 — it engages the skill, then freestyles past "read the process guide").
03-decide joined the Sonnet floor with the MCP port: with the clarity-agent
server in context, Haiku wrote the decision document but skipped the final
`--record-decision` state step (pre-MCP 3/3, post-MCP 0/3, with a preamble
warning 1/3; see its config.sh). That
matches real usage: nobody runs design conversations on Haiku, and the README
already steers users toward frontier models. An explicit `CLAUDITY_TEST_MODEL`
overrides floors everywhere.

Environment variables:

- `CLAUDITY_TEST_MODEL` — force one model for all runs (default: `haiku`,
  with per-scenario floors as above)
- `CLAUDITY_MAX_COST_USD` — budget for a sequential full run (default `3.00`)
- `CLAUDITY_SKIP_THINKER=1` — skip 04-thinker (the most expensive scenario)
- `CLAUDITY_E2E_KEEP=1` — keep scratch projects/artifacts even on pass

Tier 2 runs on whatever `claude` auth is active locally and is therefore not
wired into CI. Scenario artifacts (result JSON + stderr per run) land in a
temp directory printed at the top of the run.

## What's still not covered

Multi-turn conversational quality — the actual "pushes back with good
questions" experience — has no automated coverage; that requires either human
use or an LLM-judged eval loop (upstream's `evals/` approach), which is
exactly the inference cost this harness avoids. Treat green Tier 2 as "the
machinery works," not "the conversations are good."
