# Decision 01: Go vs Rust for the CLI

**Status:** decided (2026-06-09)

## The question

Which language should the feature-flags CLI be implemented in: Go or Rust?

## Criteria

- Time to a working tool (the team needs flag flips working soon)
- Team familiarity (two engineers know Go well; one has hobby Rust experience)
- Single-binary distribution to developer machines
- Maintenance burden for a small internal tool

## Assumptions

- The CLI is a thin client; the flags service does the heavy lifting
- Write volume is low, so raw performance is not a differentiator
- The team stays at its current size for the foreseeable future

## Options

**Go** — fast to write for this team, first-class single-binary story,
boring in the good way for an internal tool.

**Rust** — stronger type guarantees and no GC, but slower iteration for this
team and the performance headroom is unused at this scale.

## Choice

**Go.** Team familiarity and time-to-working-tool dominate; both languages
satisfy the distribution requirement, and nothing in the problem rewards
Rust's extra rigor enough to pay its learning cost here.

## Reconsideration triggers

- The solution stops being a thin client (heavy local evaluation or caching)
- Team composition shifts toward Rust experience
- Related documents change (tracked automatically via `decisionState`)
