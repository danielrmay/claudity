---
description: Work through an important decision with structured guidance
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/claudity/processes/decision-guidance.md` and follow it from the beginning. (The guide references plugin scripts via a `CLAUDE_PLUGIN_ROOT` placeholder; that variable is not set in Bash — substitute this plugin's absolute root path, which you can derive from the guide path above, when running the guide's commands.) If there is no protocol directory yet, first scaffold one with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_init.py" .` — decisions are recorded in `.clarity-protocol/decisions/`.

The decision to work through (if the user named one): $ARGUMENTS
