# Example: dev-db-snap

A real `.clarity-protocol/` packet produced by Claudity in a genuine
three-turn session (Sonnet), following the same conversation script as the
[example session transcript](../../EXAMPLE.md). Model outputs
vary run to run, so wording here differs from the quoted transcript — but
the artifacts are authentic: nothing was hand-edited.

The packet is frozen mid-project, at the end of problem clarification:

- `goal/problem.md` — the problem, including the session's reframe from
  "snapshot tool" to "team state-sharing tool"
- `goal/stakeholders.md` — the team, the maintainer, the production-data
  subjects, and the adversarial "whoever obtains the store's contents"
- `goal/requirements.md`, `goal/open-questions.md` — the criteria and the
  unknowns (snapshot size, schema-version coupling, store ownership, pull
  semantics, prod-data handling) that the next session would pick up
- `solution/`, `failures/`, `summary.md` — still templates: that's what a
  packet looks like before those phases run

Explore the dependency state:

```bash
python3 ../../scripts/protocol_status.py .
```
