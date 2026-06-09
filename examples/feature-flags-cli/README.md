# Example: feature-flags CLI

A minimal `.clarity-protocol/` packet produced while exercising Claudity's
verification loop. It shows the document structure, a recorded decision with
related-document hash tracking (`config.json` → `decisionState`), an analyzed
failure with a management plan, and an archived brainstorming pool item.

This packet is a **frozen snapshot**, kept deliberately in an interesting
state: `solution/solution.md` was edited *after* decision 01 was recorded
against it, so the status checker reports a fired reconsideration trigger for
`decision-01-go-vs-rust`. The content hashes in `config.json` reflect the
moment the snapshot was taken; if you edit the example documents, expect
staleness flags.

Run the status script against it:

```bash
python3 ../../scripts/protocol_status.py .
```
