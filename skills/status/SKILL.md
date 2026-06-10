---
name: status
description: "Show Clarity Protocol status — stale documents, recommended next step, decisions"
disable-model-invocation: true
---
Run the protocol status script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_status.py" . --agent
```

If there is no protocol directory, say so and offer `/claudity:embed`.

Summarize the output for the user in plain language (don't dump the raw report): one or two sentences on where the project stands, the recommended next step and why, and any decisions needing reconsideration. Offer to start the recommended process via Claudity's `start` skill.
