# Claudity

An AI thinking partner that pushes back — for Claude Code.

> [!WARNING]
> **Experimental — not yet human-validated.** This port from
> [microsoft/clarity-agent](https://github.com/microsoft/clarity-agent) was
> performed by AI agents (Claude Code). While the vendored staleness engine
> passes upstream's test suite, the plugin as a whole — the router skill,
> process guides, thinker subagents, and commands — has not been validated by
> a human or exercised on real projects. Expect rough edges; review before
> relying on it. See [TESTING.md](TESTING.md) for what is and isn't covered
> by automated tests.

Claudity helps you figure out whether you're building the right thing in the
first place, by asking the questions an experienced architect, product manager,
or safety engineer would ask. The answers are written down as plain markdown in
a `.clarity-protocol/` directory in your repo — committed, reviewed in PRs, and
diffed like any other source file.

Claudity is a Claude Code plugin port of Microsoft's
[Clarity Agent](https://github.com/microsoft/clarity-agent) (MIT), with the
Python/desktop harness replaced by Claude Code natives: process guides become a
skill, specialist "thinkers" become subagents, the async mailbox becomes
parallel subagent calls, and staleness tracking is a small vendored script.
Claudity is not affiliated with or endorsed by Microsoft — see
[NOTICE.md](NOTICE.md).

## Install

```
/plugin marketplace add danielrmay/claudity
/plugin install claudity@claudity
```

## Use

- `/claudity:embed` — wire the Clarity Protocol into the current project
  (scaffolds `.clarity-protocol/`, installs a snippet into `CLAUDE.md`)
- `/claudity:start` — start or resume structured thinking (the router)
- `/claudity:status` — what's stale, what's next, which decisions need review
- `/claudity:decide <topic>` — work through an important decision

Or just talk: with the plugin enabled, Claude engages the `claudity` skill when
you want to explore what to build, clarify requirements, brainstorm risks, or
make a consequential choice.

## What comes out

```text
.clarity-protocol/
├── summary.md                # what this project is, for a general audience
├── notes.md                  # shared memory: principles, cross-phase observations
├── goal/                     # problem, stakeholders, requirements, open questions
├── solution/                 # solution, architecture (with threat model), summary
├── failures/                 # failure modes, chains, management plans
├── decisions/                # decision log with criteria and rationale
└── config.json               # dependency graph + content hashes (staleness tracking)
```

Documents form a dependency graph (problem → stakeholders → requirements →
solution → failures/architecture). When an upstream document changes, Claudity
knows what downstream needs revisiting.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/pytest tests/ -q      # free, deterministic
e2e/run.sh                      # headless behavioral smoke (~$0.25 on Haiku)
```

See [TESTING.md](TESTING.md) for the full test-tier breakdown and cost model.

Vendored content is pinned to an upstream commit — see [UPSTREAM.md](UPSTREAM.md)
for the vendoring map and re-sync procedure, and [PORTING.md](PORTING.md) for
the substitution rules.

## License

MIT — see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) (portions
Copyright (c) Microsoft Corporation).
