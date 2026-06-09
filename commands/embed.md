---
description: Embed the Clarity Protocol into this project (scaffold protocol dir + CLAUDE.md snippet)
---

Embed the Clarity Protocol into the current project. Both steps are idempotent — safe to re-run.

1. **Scaffold the protocol directory:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_init.py" .
   ```

   This creates `.clarity-protocol/` (or `Clarity Protocol/` outside git repos) with template documents and `config.json`, skipping any files that already exist.

2. **Install the snippet into CLAUDE.md:** read `${CLAUDE_PLUGIN_ROOT}/skills/claudity/reference/snippet.md`, replace every `{{PROTOCOL_DIR_NAME}}` with the actual protocol directory name from step 1, and place the result in the project's root `CLAUDE.md`:
   - If `CLAUDE.md` doesn't exist, create it with the snippet as its content.
   - If it exists and contains a `<!-- claudity-begin -->` ... `<!-- claudity-end -->` block, replace that block (and only that block) with the new snippet.
   - Otherwise append the snippet to the end, separated by a blank line. Never modify content outside the markers.

3. Confirm briefly what was created, then offer to start: the user can run `/claudity:start` or just begin talking about the project. The protocol directory is meant to be committed and reviewed like any other source file.
