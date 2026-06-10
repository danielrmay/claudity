<!-- markdownlint-disable MD041 -->
<!-- claudity-begin -->
<!-- claudity-meta
schema_version: 1
protocol_dir_name: {{PROTOCOL_DIR_NAME}}
-->
<!-- Claudity manages this block; edits between the claudity-begin / claudity-end markers will be overwritten when the snippet is refreshed. Put project-specific guidance outside the markers. -->
<!-- Vendored from microsoft/clarity-agent@6b32c43 src/clarity_agent/setup/snippet.md — modified per PORTING.md rules R2, R3, R4, R5, R6, R10 (MCP tools → claudity skill and file operations) -->

## Clarity Protocol

This project uses the Clarity Protocol for structured thinking about consequential decisions — what to build and why, how it should be designed, where it might fail. Protocol documents live in `{{PROTOCOL_DIR_NAME}}/`. The Claudity plugin manages the protocol — use its `claudity` skill and commands to interact with it.

### When to engage

**Before building — think when it matters.** Two triggers:

1. *The user asks.* When they want to explore what to build, clarify requirements, brainstorm risks, or work through a decision: use the `claudity` skill (or `/claudity:start`).

2. *You recognize an inflection point.* Before making choices that would be expensive to reverse — new services, auth/trust models, data schemas, external integrations, significant API contracts — check what you plan to do against the protocol: read `{{PROTOCOL_DIR_NAME}}/decisions/decisions.md`, `goal/requirements.md`, and `solution/architecture.md` for conflicts. Don't interrupt for routine implementation. The test: "If this turns out wrong, is it a 5-minute fix or a multi-day rework?" Interrupt for the latter.

**After building — keep the record current.** After significant implementation work (new features, architectural changes), run the `/claudity:status` command (or engage the `claudity` skill) to find stale protocol documents — the plugin resolves its own script paths; do not try to locate or run them directly from this file. Update stale documents in place, and let the skill record acceptance. Record significant choices as numbered files in `{{PROTOCOL_DIR_NAME}}/decisions/` (the `claudity` skill's decision-guidance process covers the format); add newly-noticed risks to the failure pool via the `claudity` skill's failure-brainstorming process.

### Behaviors (apply throughout)

**Move quickly through what's obvious.** Many processes have multiple steps, but sometimes the answer to a step is already clear from context. When it is, just do it — write the result and present a summary for confirmation. Don't stop to ask permission at every small step. The goal is a natural conversation, not a checklist. Reserve interactive discussion for genuine ambiguity, tradeoffs, or decisions that need the user's judgment.

**Keep outputs narrative but brief.** All `.md` files in this project — protocol documents, process guides, and instructions — are repeatedly read by both humans and LLMs. They should read as smooth, concise narrative: easy to understand on first read, with nothing that wastes the reader's attention. A reader must immediately understand both the "what" and the "why." Cut anything that doesn't carry meaningful information. Since many of these files are instructions for LLMs which create further `.md` files, they should encourage the same discipline.

**Use `{{PROTOCOL_DIR_NAME}}/notes.md` as shared memory.** At the start of every process, read `{{PROTOCOL_DIR_NAME}}/notes.md` for guiding principles and cross-phase observations. When you notice something worth remembering — a design philosophy, a team constraint, an insight relevant to a future phase — add it. Tag actionable items for a specific phase with `[for: <phase>]` (e.g., `[for: failure-analysis] Authentication is a single point of failure`). When acting on a tagged item, remove it. Keep the file compact: consolidate redundant entries and remove items that have been absorbed into the relevant protocol documents.

**Generate threat model artifacts.** When writing or updating `solution/architecture.md`, include a Mermaid threat model diagram directly in the file as a fenced ` ```mermaid ` block. Write the diagram yourself; you'll produce a better diagram than any code generator. Also write `{{PROTOCOL_DIR_NAME}}/system-design.json` with structured component/flow/threat data for tooling. After failure brainstorming or analysis, write `{{PROTOCOL_DIR_NAME}}/threat-model.md` — a concise threat model summary (1-2 pages max) with top risks, severities, one-line mitigations, and single points of failure.

<!-- claudity-end -->
