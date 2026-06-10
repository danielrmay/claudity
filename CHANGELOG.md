# Changelog

All notable changes to Claudity are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is
[semver](https://semver.org/), independent of upstream (each release records
the upstream pin it tracks).

## [Unreleased]

## [0.3.0] - 2026-06-10

Tracks microsoft/clarity-agent@6b32c43 (upstream v0.1.2).

### Breaking / Migration

- **Raw failures now record to `mailboxes/failure-brainstorm/` and
  suggestions to `mailboxes/suggestions/`** (upstream's on-disk layout),
  not `failures/pool/` and `notes.md` tags. Packets created by Claudity
  ≤0.2 need no manual migration: the status engine still counts legacy
  `failures/pool/*.md` as pending analysis, and failure-analysis sweeps
  them into its consumption snapshot (PORTING.md R18). New recordings
  never write to the pool.

### Added

- **Vendored MCP server** (`scripts/mcp_server.py`, declared in the plugin's
  `.mcp.json` as the `clarity-agent` server): upstream's 8-tool surface
  (`run_clarity`, `check_decision`, `get_packet_status`,
  `read_protocol_document`, `write_protocol_document`, `record_decision`,
  `record_failure`, `record_suggestion`) with the tool bodies vendored
  near-verbatim and FastMCP replaced by a hand-rolled stdlib JSON-RPC stdio
  loop — the plugin stays zero-dependency. PORTING.md rule R17 is the
  vendoring contract. `record_failure`/`record_suggestion` gain an optional
  `source` parameter so orchestrator-recorded thinker and human findings
  keep provenance. Platform behavior verified by spike before adoption:
  plugin MCP servers work headless (`claude -p`), tools surface as
  `mcp__plugin_claudity_clarity-agent__<tool>`, subagents see plugin MCP
  tools unless restricted by `tools:` frontmatter (thinkers are restricted
  and stay read-only), and `CLAUDE_PROJECT_DIR`/`${CLAUDE_PLUGIN_ROOT}`
  plumb through as documented
- Vendored protocol libraries backing the server: `scripts/mailbox.py`
  (upstream mailbox module + CLI, near-verbatim), `scripts/brainstorm.py`
  and `scripts/suggestion.py` (recording paths; LLM-dispatch surface
  dropped per R9), with their upstream test suites
  (`tests/test_mailbox.py`, `tests/test_brainstorm.py`,
  `tests/test_suggestion.py`, `tests/test_mcp_tools.py`) and
  Claudity-original transport tests (`tests/test_mcp_protocol.py`,
  including a stdout-purity check)
- `protocol_init.py` restores upstream's suggestion-box creation
  (`mailboxes/suggestions/`)
- e2e scenario 10-record: the headless MCP canary — an ambient risk report
  must land as exactly one mailbox item via `record_failure`
- Structure tests: `.mcp.json` shape, the 8-tool surface, and `GUIDE_MAP`
  target existence


- `scripts/upstream_audit.py` (CI-enforced): fetches the pinned upstream and
  verifies every changed line in every vendored file traces to a PORTING.md
  rule; verbatim entries byte-checked. First run surfaced and fixed one
  uncited deviation (the snippet's R12 trim) and led to R16 being extended
  to cover the thinker-agent packaging
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
  behavioral suite is now 10 scenarios with 10-record

### Changed

- **Guide text reverts toward upstream verbatim** now that the MCP tools
  are real (the determinism-driven substitutions R2–R7/R13/R14 are retired;
  reversal rationale recorded in PORTING.md): the embed snippet's
  `run_clarity`/`check_decision`/`write_protocol_document`/`record_*`
  references are restored; failure-analysis consumes the mailbox with
  upstream's snapshot command (`scripts/mailbox.py snapshot`); the router
  assesses via `run_clarity` (which inlines the recommended process guide
  with `${CLAUDE_PLUGIN_ROOT}` pre-substituted) and reviews the suggestions
  mailbox; `/claudity:status` prefers `get_packet_status`. Hash recording
  now happens automatically on every `write_protocol_document` (upstream
  semantics) instead of the acceptance-gated `--record` step; the explicit
  `--record` CLI blocks in the guides remain as the safety net for
  natively-written files
- `scripts/pool_add.py` (added earlier in this cycle, never released) is
  superseded by `record_failure` and removed — upstream's tool-based design
  for failure recording is restored in its original form
- The fixture packet and its CLAUDE.md re-rendered for the mailbox layout
  and new snippet; e2e 04/07 assert mailbox artifacts


- All e2e scenario prompts enter through real product surfaces (the claudity
  skill or a command) after transcript forensics showed every
  bookkeeping-inventing session had simply failed to find the guide;
  08-management's assert now also verifies state was recorded via the script

### Changed (architecture)

- Repository structure: `e2e/` moved under `tests/e2e/` (one testing home,
  tiers distinguish); the security catalog lives with the skill that uses it
  (`skills/risks/security-catalog.csv`); the skeletal packet formerly under
  `examples/` is now honestly `tests/e2e/fixtures/feature-flags-cli` (its
  states are scenario oracles), and `examples/dev-db-snap` is a real
  Sonnet-session packet frozen at end of problem clarification, manifest-
  protected like the fixture

- Commands eliminated: every user surface is now a skill, and the 1:1 guide
  surfaces embed their vendored guide as the skill body — `/claudity:decide`,
  `/claudity:risks`, `/claudity:message` inject their guide directly (no
  pointer text, no Read hop, no fs seek); `/claudity:embed` inlines the
  CLAUDE.md snippet template (zero seeks); the router directory is
  `skills/start/` so `/claudity:start` invokes it directly. Skill bodies get
  the plugin root substituted at injection, removing the hook dependency on
  the command path. PORTING.md rule R16 covers the skill packaging. UX
  (`/claudity:*` names) unchanged.

### Reverted

- The short-lived R15 guide insertions (explicit record-state steps in
  failure-analysis and failure-management) and PORTING.md rule R15 itself.
  A controlled experiment (entry surfaces now guarantee guide-reading)
  showed guide-reading sessions record state correctly on upstream's
  original wording — the insertions fixed a misdiagnosed cause, and
  upstream's text is exonerated. The freestyle failure mode is addressed
  where it belongs, in SKILL.md ("never run a process from memory").

### Fixed

- The fidelity audit's watch entry for the security catalog pointed at a
  nonexistent upstream path (`skills/risks/...` instead of `catalogs/...`),
  so its byte-identical check had been silently skipping on a fetch 404;
  the catalog is now actually verified verbatim



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
