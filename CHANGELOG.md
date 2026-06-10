# Changelog

All notable changes to Claudity are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is
[semver](https://semver.org/), independent of upstream (each release records
the upstream pin it tracks).

## [Unreleased]

### Added

- e2e scenarios 05-09 covering solution-brainstorming, architecture-design,
  failure-analysis, failure-management, and message-clarification; the full
  behavioral suite is now 9 scenarios (~$1 on Haiku)
- PORTING.md rule R15 (additive reliability clarifications): explicit
  record-state steps and a "never hand-edit config.json" guard in the
  failure-analysis and failure-management guides, after the harness caught a
  model inventing its own config bookkeeping
- `scripts/pool_add.py`: deterministic pool recording (one correctly-placed
  file per failure), replacing hand-written pool files in all guides. The
  harness showed models repeatedly misplacing hand-written pool files —
  re-learning upstream's reason for making `record_failure` a tool

### Removed

- The experimental README warning, following the isolated real-session
  validation on Fable 5 (docs/example-session.md) on top of the automated
  harness. AI-port provenance and the verification scope remain disclosed in
  the README intro and TESTING.md.

## [0.2.0] - 2026-06-09

Tracks microsoft/clarity-agent@6b32c43 (upstream v0.1.2).

### Added

- New-user onboarding: README quickstart, prerequisites, cost and privacy
  notes, uninstall instructions, and a real example session transcript
  (docs/example-session.md, recorded on Fable 5)
- Contributor docs: CONTRIBUTING.md (upstream-first policy, adding-a-thinker
  recipe), code of conduct, issue and PR templates

- Three-tier test harness: structural pytest suite, `claude plugin validate`
  in CI, headless e2e smoke scenarios with a hard cost budget (see TESTING.md)
- Upstream watcher: nightly GitHub Action that compares the pinned upstream
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
