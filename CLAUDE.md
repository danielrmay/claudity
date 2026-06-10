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
  upstream.json, and UPSTREAM.md agree.
- **Zero dependencies**: python3 stdlib only, nothing pip-installed — including
  the MCP server (hand-rolled stdio JSON-RPC; "Transport" note in PORTING.md).
- **Windows portability**: all file I/O passes `encoding="utf-8"` (the locale
  default corrupts unicode markdown) and path comparisons in tests use
  `as_posix()`. The windows-latest CI job enforces both under cp1252 — never
  set PYTHONUTF8 in CI; it masks exactly these bugs. The e2e harness is
  POSIX-only (its tests skip on win32).
- **Versioning**: bump `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` together (test-enforced). Releases via
  `claude plugin tag`.

## Testing

- Tier 1 (free, run always): `.venv/bin/python -m pytest tests/ -q` plus the
  audit above. Tier 0: `claude plugin validate .`.
- Tier 2 (paid, local): `tests/e2e/run.sh` — see TESTING.md for model floors
  and stress mode. Sessions run against a frozen, hash-verified snapshot of
  the plugin, never this repo — plugin-content edits during a background run
  are safe, but don't edit the harness scripts (`tests/e2e/`) mid-run.
- If the post-run repo-dirty warning ever fires, the snapshot indirection
  leaked — investigate, don't shrug.
- `scripts/mcp_server.py` edits need a session restart (or `/reload-plugins`)
  interactively; pytest spawns fresh server processes, so tests always see
  current code.

## Behavioral changes need behavioral evidence

Guide/skill text changes that claim to fix model behavior need e2e
measurement (stress a scenario before and after — the model-floor notes in
`tests/e2e/scenarios/*/config.sh` are the precedent). Guide-content
improvements belong upstream first (CONTRIBUTING.md).
