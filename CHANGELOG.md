# Changelog

All notable changes to Claudity are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is
[semver](https://semver.org/), independent of upstream (each release records
the upstream pin it tracks).

## [Unreleased]

### Added

- Three-tier test harness: structural pytest suite, `claude plugin validate`
  in CI, headless e2e smoke scenarios with a hard cost budget (see TESTING.md)
- Upstream watcher: biweekly GitHub Action that compares the pinned upstream
  commit against `microsoft/clarity-agent` main, filtered to the vendored
  path set, and opens an `upstream-sync` issue when a re-sync is needed
- `upstream.json`: machine-readable pin + vendored-path watch list
  (single source of truth, enforced by CI)
- Example packet now includes the `decision-01-go-vs-rust` decision document
  and intentionally demonstrates a fired reconsideration trigger

### Changed

- The CLAUDE.md snippet installed by `/claudity:embed` routes status checks
  through `/claudity:status` instead of invoking plugin script paths that are
  undefined outside plugin context
- Failure-brainstorming guide explicitly forbids writing brainstormed
  failures into `failures/` or `failures/pool/archive/` (found via e2e on
  Haiku)

## [0.1.0] - 2026-06-09

Initial port. Tracks microsoft/clarity-agent@6b32c43 (upstream v0.1.2).

### Added

- Router skill (`claudity`) replacing upstream's `clarity-agent.md` process
- 11 process guides vendored near-verbatim with PORTING.md substitutions
- 6 thinker subagents (read-only) replacing upstream's async mailbox thinkers
- Vendored staleness engine (`scripts/protocol_status.py`) and packet
  scaffolder (`scripts/protocol_init.py`), stdlib-only
- Commands: `/claudity:start`, `embed`, `status`, `decide`, `risks`, `message`
- Security catalog (OWASP LLM/Agentic Top 10, STRIDE)
- MIT licensing with Microsoft attribution (NOTICE.md), pinned upstream
  vendoring map (UPSTREAM.md), substitution rules (PORTING.md)
