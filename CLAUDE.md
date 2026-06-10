# Claudity — contributor context

Claude Code plugin port of Microsoft's Clarity Agent. Most files here are
VENDORED from microsoft/clarity-agent under a strict porting contract — read
the contract before editing anything:

- [PORTING.md](PORTING.md) — substitution rules; every deviation in a vendored
  file must trace to a rule
- [UPSTREAM.md](UPSTREAM.md) — pin, vendoring map, re-sync and release procedure
- [TESTING.md](TESTING.md) — the tiered harness and what each tier proves
- [CONTRIBUTING.md](CONTRIBUTING.md) — upstream-first policy, adding thinkers

## Invariants

- **Vendored files**: after touching anything in the upstream.json watch set,
  run `python3 scripts/upstream_audit.py` — unexplained changed lines fail CI.
  Vendored headers carry the pin; pin-consistency tests fail until headers,
  upstream.json, NOTICE.md, and UPSTREAM.md agree.
- **Zero dependencies**: everything runs on python3 stdlib. Nothing is pip-
  installed, ever — that includes the MCP server (hand-rolled stdio JSON-RPC,
  see the "Transport" note in PORTING.md).
- **Versioning**: bump `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` together (test-enforced). Releases via
  `claude plugin tag`.

## Testing

- Tier 1 (free, run always): `.venv/bin/python -m pytest tests/ -q` plus the
  audit above. Tier 0: `claude plugin validate .`.
- Tier 2 (paid, local): `tests/e2e/run.sh` — see TESTING.md for model floors
  and stress mode. **Never modify repo files while a background e2e run is in
  flight** (sessions read the plugin live; mid-run edits invalidate results).
- E2e sessions know this repo's path and can stray into it: check `git status`
  after runs; the manifest tests guard the fixture and showcase packets.
- `scripts/mcp_server.py` edits need a session restart (or `/reload-plugins`)
  to take effect interactively; pytest drives fresh server processes, so tests
  always see current code.

## Behavioral changes need behavioral evidence

Guide/skill text changes that claim to fix model behavior need e2e
measurement (stress a scenario before and after — see the model-floor notes in
`tests/e2e/scenarios/*/config.sh` for the precedent). Guide-content
improvements belong upstream first (CONTRIBUTING.md).
