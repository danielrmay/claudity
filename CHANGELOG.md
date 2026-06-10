# Changelog

All notable changes to Claudity are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is
[semver](https://semver.org/), independent of upstream (each release records
the upstream pin it tracks).

## [Unreleased]

### Changed (architecture)

- Commands eliminated: every user surface is now a skill, and the 1:1 guide
  surfaces embed their vendored guide as the skill body — `/claudity:decide`,
  `/claudity:risks`, `/claudity:message` inject their guide directly (no
  pointer text, no Read hop, no fs seek); `/claudity:embed` inlines the
  CLAUDE.md snippet template (zero seeks); the router directory is
  `skills/start/` so `/claudity:start` invokes it directly. Skill bodies get
  the plugin root substituted at injection, removing the hook dependency on
  the command path. PORTING.md rule R16 covers the skill packaging. UX
  (`/claudity:*` names) unchanged.

### Added

- e2e v2: scenarios are scripted multi-turn persona conversations (verbatim
  user messages via `claude -p --resume`, acceptance as a real user turn)
  instead of single prompts with stage directions; `--parallel` suite mode
  and `--stress <scenario> <n>` pass-rate mode; per-scenario model floors
  (ambient conversational scenarios test on Sonnet: measured 4/4 vs 2/6 on
  Haiku, which engages the skill then freestyles past the guide)
- The example packet now includes the embedded CLAUDE.md snippet, as every
  real embedded project has

- e2e scenarios 05-09 covering solution-brainstorming, architecture-design,
  failure-analysis, failure-management, and message-clarification; the full
  behavioral suite is now 9 scenarios
- `scripts/pool_add.py`: deterministic pool recording (one correctly-placed
  file per failure), replacing hand-written pool files in all guides —
  restoring upstream's tool-based design for `record_failure`

### Reverted

- The short-lived R15 guide insertions (explicit record-state steps in
  failure-analysis and failure-management) and PORTING.md rule R15 itself.
  A controlled experiment (entry surfaces now guarantee guide-reading)
  showed guide-reading sessions record state correctly on upstream's
  original wording — the insertions fixed a misdiagnosed cause, and
  upstream's text is exonerated. The freestyle failure mode is addressed
  where it belongs, in SKILL.md ("never run a process from memory").

### Changed

- All e2e scenario prompts enter through real product surfaces (the claudity
  skill or a command) after transcript forensics showed every
  bookkeeping-inventing session had simply failed to find the guide;
  08-management's assert now also verifies state was recorded via the script

### Fixed

- `CLAUDE_PLUGIN_ROOT` is substituted only when skill/command content is
  injected — it is NOT set in the Bash environment, so a model re-typing the
  placeholder from a Read-from-disk guide ran scripts against an empty path
  (silently, when piped through `tail`). Surface skills now inject their
  content with the root pre-resolved, and the router instructs substitution
  for the on-demand guides

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
