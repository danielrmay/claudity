# Testing

*For contributors and maintainers. Users of the plugin don't need anything here.*

The harness is tiered so inference is paid for only where behavior is
model-driven. Tiers 0 and 1 are free and run in CI on every push; Tier 2 is a
small headless smoke suite with a hard cost budget, run locally on demand.

| Tier | What | Cost | When |
| ---- | ---- | ---- | ---- |
| 0 | `claude plugin validate .` + component inventory (`claude --plugin-dir . plugin details claudity`) | free | CI, every push |
| 1 | `pytest tests/` — 71 vendored status-engine tests + structural tests (manifests, frontmatter, cross-reference integrity, porting lints, init↔staleness coupling) | free | CI, every push |
| 2 | `e2e/run.sh` — 9 headless scenarios with deterministic artifact assertions | ~$1 on Haiku | locally, before a release or after touching SKILL.md / processes / commands / agents |

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
e2e/run.sh          # all scenarios
e2e/run.sh 01       # one scenario by prefix
```

Each scenario runs `claude -p` in a throwaway project with the plugin loaded
via `--plugin-dir` (nothing is installed into your real config), then asserts
on **artifacts** — files created, `config.json` state, status-script output —
never on LLM-judged transcripts. Scenario prompts must enter through real
product surfaces (a `/claudity:*` command or the skill): a prompt that says
"read the guide" without a path tests a phantom entry that no user docs
suggest, and the model may never find the guide. Transcript forensics across
five sessions showed this cleanly — every session that hand-invented config
bookkeeping had failed to find the guide, and every session that read the
guide recorded state correctly. Worse, a model that can't find the guide
improvises something plausible instead of stopping, which can slip past
asserts that don't check recording (08-management did exactly this twice
before its assert was tightened). A per-scenario cost table is printed from
the CLI's `total_cost_usd`, and the suite fails if the total exceeds the
budget.

| Scenario | Verifies |
| -------- | -------- |
| 01-embed | `/claudity:embed` scaffolds the packet (9 empty docs) and installs the CLAUDE.md snippet with markers and no unexpanded placeholders |
| 02-routing | `/claudity:status` runs the status script and correctly relays the recommended next process for a fixture packet |
| 03-decide | `/claudity:decide` produces a real decision document, updates the index, and records `decisionState` (status `decided`, non-empty `relatedDocs`) |
| 04-thinker | failure-brainstorming launches the `general-thinker` subagent and persists its findings to `failures/pool/`, flipping the status engine to recommend `failure-analysis` |
| 05-solution | solution-brainstorming fills a blanked `solution.md` + `solution-summary.md` with real content and records them as current |
| 06-architecture | architecture-design writes `architecture.md` with the Mermaid threat-model block plus a valid `system-design.json`, and records state |
| 07-analysis | failure-analysis snapshots seeded pool files to `pool/archive/`, produces analyzed `failure-NN` documents and a real index, and records state |
| 08-management | failure-management replaces a seeded placeholder `## Management Plan` with a real plan; the status engine stops recommending the phase |
| 09-message | message-clarification writes a non-template general-audience `summary.md` and records it |

Discovery (`discovery-research` / `discovery-prototype`) remains uncovered:
their outputs are investigation programs and disposable prototypes with no
cheap deterministic artifact contract.

Environment variables:

- `CLAUDITY_TEST_MODEL` — model for runs (default `haiku`). Haiku is the
  default on purpose: it's the cheapest and the most demanding test of the
  guides — if Haiku can follow them, larger models will. In practice Haiku
  failures have mostly exposed real guide ambiguities (e.g. it wrote
  brainstormed failures into `failures/` and then `pool/archive/` until the
  guide explicitly forbade both). Re-run a failure once on `sonnet`: if
  Sonnet passes, treat it as a guide-clarity bug, not a flake.
- `CLAUDITY_MAX_COST_USD` — budget for a full run (default `1.50`)
- `CLAUDITY_SKIP_THINKER=1` — skip 04-thinker (the most expensive scenario)

Tier 2 runs on whatever `claude` auth is active locally and is therefore not
wired into CI. Scenario artifacts (result JSON + stderr per run) land in a
temp directory printed at the top of the run.

## What's still not covered

Multi-turn conversational quality — the actual "pushes back with good
questions" experience — has no automated coverage; that requires either human
use or an LLM-judged eval loop (upstream's `evals/` approach), which is
exactly the inference cost this harness avoids. Treat green Tier 2 as "the
machinery works," not "the conversations are good."
