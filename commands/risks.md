---
description: Brainstorm failure modes and risks with specialist thinker subagents
---

Run the Claudity failure pipeline. Read `${CLAUDE_PLUGIN_ROOT}/skills/claudity/processes/failure-brainstorming.md` and follow it from the beginning. (The guide references plugin scripts via a `CLAUDE_PLUGIN_ROOT` placeholder; that variable is not set in Bash — substitute this plugin's absolute root path, which you can derive from the guide path above, when running the guide's commands.) It requires a protocol directory with at least a real problem statement — if that's missing, say so and route through the `claudity` skill (problem clarification) first.

If the brainstorming pool already has pending items, offer failure-analysis instead (the status script's Process Availability section shows which phase is recommended).

Focus area, if the user named one: $ARGUMENTS
