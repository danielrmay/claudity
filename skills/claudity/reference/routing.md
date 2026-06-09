<!-- Vendored from microsoft/clarity-agent@6b32c43 processes/clarity-agent.md (Step 3 routing detail) — modified per PORTING.md rules R1, R10 -->

# Routing detail

Read this when assessing an existing project (SKILL.md Step 3). It covers what
the status output alone can't decide: quality judgment, discovery routing,
narrative freshness, and decision reconsideration.

## Stale or empty documents

Upstream problems need addressing before downstream documents are meaningful.
Weave it into the conversation:

> "We have a solid problem statement, but we haven't really talked about who the stakeholders are. Want to start there?"

Or if something downstream is stale:

> "It looks like the requirements shifted since we wrote the solution — we should probably revisit that."

## Everything mechanically current — assess quality

Read the documents in dependency order. Things can be technically current but
qualitatively rough — vague, incomplete, missing important details:

| Document | Signs it needs work |
| -------- | ------------------- |
| `goal/problem.md` | Vague problem, untestable success criteria |
| `goal/stakeholders.md` | Missing stakeholders, needs and concerns unclear |
| `goal/requirements.md` | Requirements not specific, not testable, not traced to stakeholders |
| `goal/open-questions.md` | Has unresolved questions (status: open or investigating) — see below |
| `solution/solution.md` | No clear approach, not justified against the problem |
| `failures/failures.md` | Failure modes not systematically explored, or identified failures lack management plans |
| `solution/architecture.md` | Technical decisions undocumented or unjustified |
| `summary.md` / `messaging.md` | The narrative reads like a spec, doesn't tell a story, or doesn't match the current problem/solution |
| `decisions/decisions.md` | Important choices undocumented, or pending decisions unresolved |

If something seems rough, suggest it gently — a judgment call, not a finding:

> "Everything's in place, though the success criteria feel a bit vague to test against. Want to sharpen those up, or are you happy with where things are?"

If everything looks solid: "Things look well-developed. Ready to move forward, or is there something you'd like to revisit?"

## Narrative freshness

The staleness system catches upstream document changes, but not when the user
has learned something from the world — a pitch that fell flat, a question from
a skeptic. If `messaging.md` exists (or the project has been through
message-clarification), ask directly:

> "Have you talked to anyone about this since we last worked on the narrative? Any reactions that surprised you, or things that were hard to explain?"

A "yes" is a reason to suggest **message-clarification**, even with no stale
documents. Messaging improves through contact with reality, not polishing in
isolation.

## Unresolved open questions — discovery routing

Questions with status "open" or "investigating" signal a **discovery**
situation: fundamental unknowns that would change the solution approach.
Handle with the same priority as a stale upstream document:

> "There are some open questions from problem clarification that we haven't resolved yet — [brief summary]. Want to work on those before we move into solutions, or has anything changed?"

Route by the question's strategy field:

- **"prototyping"** → **discovery-prototype** (minimal, disposable prototype to test a hypothesis)
- **"research"** → **discovery-research** (structured investigation program)
- **"thinking"** → continue **problem-clarification** (deeper conversation is the method)
- **Exploratory/rapid-prototyping-at-scale phase** (noted in open-questions.md) → **solution-brainstorming**, framed as building experimentation infrastructure, not a final solution

Don't block all downstream work if questions are independent of it. A question
about database scalability doesn't prevent working on the authentication
design — use the "Why it matters" field to judge what each question blocks.

## Process routing

The status output's Process Availability section shows which processes are
recommended, available, and unavailable with reasons. When a process is
recommended, the right action is to **hand off to that process guide**, not to
attempt the task directly. If multiple processes are recommended, the
Recommended Next Step (dependency-graph walk) indicates priority. Starting
analysis on a partial pool is fine — failure analysis can run incrementally.

## Decisions

Decisions are cross-cutting — they arise at any point, not just at the end.
If a choice comes up during any process, note it in the decisions log and use
**decision-guidance** if it deserves careful analysis.

**Decision reconsideration** works in three stages:

1. **Preliminary triggers.** The status output reports when documents a
   decision was grounded in have changed. Don't analyze them during normal
   assessment — just note that they exist.
2. **Trigger analysis.** When nothing more pressing remains (all documents
   current, no urgent quality issues), review triggered decisions: read the
   decision's assumptions and the changed documents, and assess whether the
   change is material. If it is, mark the decision `reconsideration-needed`
   and note why in the decision file. If it isn't, re-record the decision
   (same status, no `--related-docs`) to re-snapshot the hashes and clear the
   trigger:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/protocol_status.py" . --record-decision <id> --status decided
   ```

3. **Reconsideration.** Decisions marked `reconsideration-needed` surface to
   the user at the same priority as any other action — not buried. Say which
   decision needs revisiting and why, and offer **decision-guidance**.
