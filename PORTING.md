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
| R17 | The upstream MCP server (`src/clarity_agent/mcp/server.py`, FastMCP) and tool invocations in guide text (MCP tool references and `python -m clarity_agent.ai_actions.*` CLI blocks) | The vendored stdlib server `scripts/mcp_server.py`, declared in the plugin's `.mcp.json` as the `clarity-agent` server, exposing the same 8 tools. Guide text invokes the tools by their upstream names (`record_failure`, `record_suggestion`, `run_clarity`, …). Server adaptations (each noted in its docstring): FastMCP → hand-rolled stdlib JSON-RPC stdio loop; `CLARITY_PROJECT_DIR` → `CLAUDE_PROJECT_DIR` (compat fallback kept); agent-dir → plugin layout via `CLAUDITY_PLUGIN_ROOT` + a guide map; served guide text gets frontmatter stripped and `${CLAUDE_PLUGIN_ROOT}` substituted; upstream's internal (non-tool) functions descoped (no Claude Code consumer); the 6 MCP resources are served so they stay @-mentionable (`clarity://behaviors` reads the CLAUDE.md claudity block read-only instead of refreshing AGENTS.md; thinker guides serve frontmatter-stripped). The tool-surface extensions live in their own section below — they are protocol improvements, not porting substitutions |

### Transport: stdio shim, not FastMCP

Upstream's server runs on FastMCP, which requires the `mcp` package (plus
pydantic) installed in the user's Python — a dependency the plugin cannot
install, breaking Claudity's python3-stdlib-only contract. A FastMCP vendor
would not be a straight vendor anyway: every R17 adaptation (import
redirection, project/agent-dir resolution, guide serving) applies
identically; the only delta is ~200 lines of hand-rolled JSON-RPC stdio
transport at the bottom of `scripts/mcp_server.py`, covered by
`tests/test_mcp_protocol.py`. Revisit if Claude Code plugins gain dependency
management or upstream ships a stdlib transport.

### Server extensions (upstream candidates)

Three additions to the upstream tool surface. They are deliberate protocol
improvements with e2e evidence behind them, not porting substitutions, and
are candidates for proposing upstream per CONTRIBUTING's upstream-first
policy (each is also flagged in the server docstring):

- **`source` on `record_failure`/`record_suggestion`** (upstream hardcodes
  `source="mcp"`). The orchestrator records on behalf of thinker subagents
  and human contributors, so provenance must travel through the tool call;
  upstream's own guides assume a source can be stated, and the failure
  documents carry `**Source:**` lines that analysis reads.
- **`related_docs` on `record_decision`** (upstream's tool records no
  grounding). Without related docs the staleness engine can never flag a
  tool-recorded decision for reconsideration — e2e caught a pure-MCP decide
  session producing a permanently trigger-less decision.
- **Full-stem `decisionState` keys** (upstream extracts only the number
  prefix). Upstream's tool and its own decision-guidance CLI disagree on id
  format; a session that used both double-recorded under `02` and
  `decision-02-<slug>`. The tool now writes the same key the CLI does.

### Retired rules

R2–R7, R13, and R14 (the Claude Code-native substitutions for upstream's MCP
tools: status via script, Read/Write tools plus acceptance-gated `--record`,
decision/failure/suggestion recording via scripts and notes.md, pool files
instead of mailboxes) were retired when the vendored MCP server landed —
upstream's tool references in guide text are now correct as written, give or
take R17. R13 was folded into R1. R18 (a legacy-pool dual-read) existed
briefly on the 0.3.0 branch and was removed before release — treat the
number as retired. The 0.3.0 CHANGELOG entry records the reversals and
their original rationale.

## Vendored Python and tests

`scripts/protocol_status.py`, `scripts/protocol_init.py`, `scripts/mailbox.py`,
`scripts/brainstorm.py`, `scripts/suggestion.py`, `scripts/mcp_server.py`, and
the vendored tests carry their modification notes in their own docstrings.
Summary of behavioral deviations:

- **Async locks ignored.** Claudity thinkers are synchronous subagents, so
  `brainstorm_in_progress` is always false. A lockfile left by a Clarity
  harness does not block brainstorming.
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
