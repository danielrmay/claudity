# Porting rules

*For contributors and maintainers. Users of the plugin don't need anything here.*

Claudity vendors Clarity Agent's process guides and thinkers near-verbatim,
changing only how they touch the outside world: Clarity's Python harness, MCP
tools, and async mailboxes become Claude Code natives (Bash invocations of the
vendored scripts, file tools, and subagents). Every deviation in a vendored
file must trace to a rule below; anything else is upstream text.

Each vendored markdown file starts with a header comment:

```
<!-- Vendored from microsoft/clarity-agent@6b32c43 <upstream path> — modified per PORTING.md rules R1, R4, ... -->
```

## Substitution rules

| # | Upstream construct | Claudity replacement |
|---|---|---|
| R1 | `python -m clarity_agent.protocol.packet_status <args>` | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_status.py" <project_dir> <args>` via Bash |
| R2 | MCP `get_packet_status` / `run_clarity` status assessment | R1 with `--agent` (or `--json`) |
| R3 | MCP `read_protocol_document(doc)` | Read tool on `.clarity-protocol/<doc>` |
| R4 | MCP `write_protocol_document(doc)` | Write/Edit tool on the file, then R1 `--record <doc>` **only after the user accepts the document** — recording on every edit would destroy staleness semantics |
| R5 | MCP `record_decision(...)` | Write `decisions/decision-NN-<slug>.md` (NN = highest existing + 1), update the `decisions/decisions.md` index, then R1 `--record-decision <id> --status <s> --related-docs <docs>` |
| R6 | MCP `record_failure(...)` / `ai_actions.brainstorm record-failure` | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pool_add.py" <project_dir> <source>` (one pool file per failure; never hand-written — the e2e harness showed models misplace hand-written pool files, re-learning why upstream made this a tool) |
| R7 | MCP `record_suggestion(...)` / `ai_actions.suggestion record` | Append to `.clarity-protocol/notes.md` tagged `[for: <phase>]` |
| R8 | `run_clarity(process)` / "switch to process X" | Read `${CLAUDE_PLUGIN_ROOT}/skills/start/processes/<x>.md` and continue in-conversation |
| R9 | `read_thinker_guide(name)` + mailbox dispatch, lockfiles, polling | Launch the named thinker subagent (`agents/<name>.md`) via the Agent tool — in parallel when running several; the orchestrator persists each subagent's returned findings via `pool_add.py` (R6) |
| R10 | References to `clarity-agent.md` (the upstream router) | References to the Claudity router skill (`/claudity:start`) |
| R11 | Paths to `skills/risks/security-catalog.csv` or other plugin files inside thinker/process text | The orchestrator resolves the absolute path under `${CLAUDE_PLUGIN_ROOT}` and injects it into the subagent prompt (env vars are not expanded inside agent bodies) |
| R12 | Instructions specific to the Clarity UI, transcripts, docx/packet export, or installer | Deleted, with an HTML comment `<!-- deleted per R12: ... -->` marking the spot |
| R13 | `python -m clarity_agent.protocol.initialize <dir>` | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_init.py" <project_dir>` via Bash |
| R14 | `python -m clarity_agent.protocol.mailbox snapshot/write ...` | Move processed pool files to `failures/pool/archive/<YYYY-MM-DD>/`; write new raw failures as plain files in `failures/pool/` |
| R16 | Vendored units that ARE a Claude Code component: guides/templates with a 1:1 user entry (decision-guidance, failure-brainstorming, message-clarification, the agent snippet) and the six thinkers | Packaged as skills/agents: Claude Code frontmatter, a short task preamble, a `## Metadata` block carrying the upstream frontmatter fields, and (thinkers) the standardized `## Output format` contract replacing upstream's tool instructions (with R9); the vendored methodology text remains governed by the other rules. (R15 is retired — see CHANGELOG.) |

## Vendored Python and tests

`scripts/protocol_status.py`, `scripts/protocol_init.py`, and
`tests/test_protocol_status.py` carry their modification notes in their own
docstrings. Summary of behavioral deviations:

- **Async locks ignored.** Claudity thinkers are synchronous subagents, so
  `brainstorm_in_progress` is always false. A lockfile left by a Clarity
  harness does not block brainstorming.
- **Brainstorm pool.** Pending-analysis items are counted from both the
  upstream `mailboxes/failure-brainstorm/` (Clarity-made packets) and
  Claudity's `failures/pool/*.md`.
- **Init writes no mailboxes and no AGENTS.md block.** The CLAUDE.md snippet
  is installed by `/claudity:embed`; suggestion mailboxes are replaced by
  `notes.md` entries (R7).
