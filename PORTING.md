# Porting rules

*For contributors and maintainers. Users of the plugin don't need anything here.*

Claudity vendors Clarity Agent's process guides, thinkers, MCP server, and
protocol libraries near-verbatim, changing only how they touch the outside
world: Clarity's MCP server runs as a plugin-provided stdlib server (the
`clarity-agent` server in `.mcp.json`), its Python CLIs become Bash
invocations of the vendored scripts, and its async thinker mailboxes become
parallel Claude Code subagents. Every deviation in a vendored file must
trace to a rule below; anything else is upstream text.

Each vendored markdown file starts with a header comment:

```
<!-- Vendored from microsoft/clarity-agent@6b32c43 <upstream path> — modified per PORTING.md rules R1, R17, ... -->
```

## Substitution rules

| # | Upstream construct | Claudity replacement |
|---|---|---|
| R1 | `python -m clarity_agent.protocol.<module> <args>` | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py" <args>` via Bash (packet_status → protocol_status.py, initialize → protocol_init.py, mailbox → mailbox.py) |
| R8 | "switch to process X" / references to reading process guides | Read `${CLAUDE_PLUGIN_ROOT}/skills/start/processes/<x>.md` (or the skill body for guides packaged per R16) and continue in-conversation; `run_clarity` also inlines the recommended guide |
| R9 | `read_thinker_guide(name)` / `recommend_deeper_analysis` + mailbox dispatch, lockfiles, polling | Launch the named thinker subagent (`agents/<name>.md`) via the Agent tool — in parallel when running several; the orchestrator persists each subagent's returned findings via the `record_failure` / `record_suggestion` tools, passing `source: <thinker-name>`. (Thinker agents carry `tools: Read, Grep, Glob` and do not record directly, though plugin MCP tools are visible to unrestricted subagents.) |
| R10 | References to `clarity-agent.md` (the upstream router) | References to the Claudity router skill (`/claudity:start`) |
| R11 | Paths to `skills/risks/security-catalog.csv` or other plugin files inside thinker/process text | The orchestrator resolves the absolute path under `${CLAUDE_PLUGIN_ROOT}` and injects it into the subagent prompt (env vars are not expanded inside agent bodies) |
| R12 | Instructions specific to the Clarity UI, transcripts, docx/packet export, installer, or per-project MCP configuration (`.vscode/mcp.json`, `clarity embed`) | Deleted or replaced with "the Claudity plugin provides these tools" wording; deletions marked `<!-- deleted per R12: ... -->` |
| R16 | Vendored units that ARE a Claude Code component: guides/templates with a 1:1 user entry (decision-guidance, failure-brainstorming, message-clarification, the agent snippet) and the six thinkers | Packaged as skills/agents: Claude Code frontmatter, a short task preamble, a `## Metadata` block carrying the upstream frontmatter fields, and (thinkers) the standardized `## Output format` contract replacing upstream's tool instructions (with R9); the vendored methodology text remains governed by the other rules. (R15 is retired — see CHANGELOG.) |
| R17 | The upstream MCP server (`src/clarity_agent/mcp/server.py`, FastMCP) and tool invocations in guide text (MCP tool references and `python -m clarity_agent.ai_actions.*` CLI blocks) | The vendored stdlib server `scripts/mcp_server.py`, declared in the plugin's `.mcp.json` as the `clarity-agent` server, exposing the same 8 tools. Guide text invokes the tools by their upstream names (`record_failure`, `record_suggestion`, `run_clarity`, …). Server adaptations (each noted in its docstring): FastMCP → hand-rolled stdlib JSON-RPC stdio loop; `CLARITY_PROJECT_DIR` → `CLAUDE_PROJECT_DIR` (compat fallback kept); agent-dir → plugin layout via `CLAUDITY_PLUGIN_ROOT` + a guide map; served guide text gets frontmatter stripped and `${CLAUDE_PLUGIN_ROOT}` substituted; upstream's internal (non-tool) functions and 6 MCP resources descoped; `record_failure`/`record_suggestion` gain an optional `source` parameter so orchestrator-recorded findings keep thinker/human provenance |
| R18 | — (Claudity-only migration) | Packets created by Claudity ≤0.2 keep raw failures in `failures/pool/*.md`. The status engine counts them as pending-analysis alongside the mailbox, and failure-analysis sweeps them into the consumption snapshot (one parenthetical in its Step 1). New recordings never write to the pool. |

### Retired rules

R2–R7, R13, and R14 (the Claude Code-native substitutions for upstream's MCP
tools: status via script, Read/Write tools plus acceptance-gated `--record`,
decision/failure/suggestion recording via scripts and notes.md, pool files
instead of mailboxes) were retired when the vendored MCP server landed —
upstream's tool references in guide text are now correct as written, give or
take R17. R13 was folded into R1. The 0.3.0 CHANGELOG entry records the
reversals and their original rationale.

## Vendored Python and tests

`scripts/protocol_status.py`, `scripts/protocol_init.py`, `scripts/mailbox.py`,
`scripts/brainstorm.py`, `scripts/suggestion.py`, `scripts/mcp_server.py`, and
the vendored tests carry their modification notes in their own docstrings.
Summary of behavioral deviations:

- **Async locks ignored.** Claudity thinkers are synchronous subagents, so
  `brainstorm_in_progress` is always false. A lockfile left by a Clarity
  harness does not block brainstorming.
- **Legacy brainstorm pool (R18).** Pending-analysis items are counted from
  both `mailboxes/failure-brainstorm/` and the legacy Claudity ≤0.2
  `failures/pool/*.md`.
- **Init restores the suggestion box; no AGENTS.md block.** `protocol_init.py`
  creates `mailboxes/` and the permanent suggestions mailbox like upstream;
  the CLAUDE.md snippet is installed by `/claudity:embed` instead of the
  upstream AGENTS.md refresh.
- **LLM-dispatch surface stripped.** `brainstorm.py`/`suggestion.py` keep only
  the recording path (R9 replaces the thinker dispatch; the API-backend tool
  handlers have no Claude Code consumer).
- **Stdlib `mailbox` shadowing.** `scripts/mailbox.py` shadows Python's stdlib
  `mailbox` module for code importing with `scripts/` on `sys.path`; nothing
  in this repo uses the stdlib module.
