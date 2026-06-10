# 🧊 Claudity

An AI thinking partner that pushes back, for Claude Code.

> 🧑‍💻 &nbsp;**You:** I want to build a CLI tool that snapshots and restores
> local dev databases.
>
> 🧊 &nbsp;**Claudity:** I can already imagine the tool — but I want to make
> sure I understand the *pain* first, because "a snapshot CLI" is an
> artifact. [...] The magic-wand test: if snapshot/restore already existed
> and worked perfectly, what would you actually do differently day-to-day?
>
> 💬 &nbsp;*a few answers later...*
>
> 🧊 &nbsp;**Claudity:** **You're not building a snapshot tool — you're
> building a state-sharing tool.** Every detail you just gave — push/pull,
> names like `bug-1234`, credentials, "who has which version" — describes a
> *distribution* problem. [...] What's actually *in* these dev databases?
> [...] if dev DBs ever contain production-derived rows [...] then
> `snap push` is quietly building an unaudited archive of customer data,
> copied to a bucket and six laptops.

✨ Real session, abridged — [full transcript](docs/example-session.md). Three
turns in, the project has a different shape, a privacy requirement nobody had
thought about, and all of it written to versionable markdown in the repo.

Claudity helps you figure out whether you're building the right thing in the
first place, by asking the questions an experienced architect, product manager,
or safety engineer would ask. The answers are written down as plain markdown
in a `.clarity-protocol/` directory in your repo: committed, reviewed in PRs,
and diffed like any other source file. Nothing lives only in a chat
transcript.

Claudity is a Claude Code plugin port of Microsoft's
[Clarity Agent](https://github.com/microsoft/clarity-agent) (MIT), with the
Python/desktop harness replaced by Claude Code natives: process guides become a
skill, specialist "thinkers" become subagents, the async mailbox becomes
parallel subagent calls, and staleness tracking is a small vendored script.
The port was performed by AI agents (Claude Code) and is covered by a tiered
automated test harness plus real-session runs; see [TESTING.md](TESTING.md)
for exactly what is and isn't verified. Claudity is an independent project.
It is not affiliated with or endorsed by Microsoft or Anthropic. See
[NOTICE.md](NOTICE.md).

## Prerequisites

- Claude Code with plugin support (a recent version)
- `python3` 3.10+ on PATH (the bundled scripts are stdlib-only)
- `git` (the protocol directory is designed to be committed)
- Tested on macOS and Linux; Windows is untested

## Install

```
/plugin marketplace add danielrmay/claudity
/plugin install claudity@claudity
```

## Quickstart

1. In your project, run `/claudity:embed`. This scaffolds `.clarity-protocol/`
   with template documents and adds a managed block to your `CLAUDE.md`.
2. Just describe what you're building (or run `/claudity:start`). Claudity
   asks questions and writes what it learns into the protocol documents as
   you talk; ending a session mid-thought loses nothing.
3. Next session, run `/claudity:status` (or just keep talking): it reads the
   document state and picks up where you left off.

The common path is problem clarification → solution → failure analysis →
architecture; everything else (discovery, decisions, messaging) is invoked on
demand. See the [example session](docs/example-session.md) for what the first
conversation looks like, and [tests/e2e/fixtures/feature-flags-cli](tests/e2e/fixtures/feature-flags-cli)
for a complete protocol directory.

## Use

- `/claudity:embed` wires the Clarity Protocol into the current project
  (scaffolds `.clarity-protocol/`, installs a snippet into `CLAUDE.md`)
- `/claudity:start` starts or resumes structured thinking (the router)
- `/claudity:status` shows what's stale, what's next, and which decisions need review
- `/claudity:decide <topic>` works through an important decision
- `/claudity:risks` brainstorms failure modes with specialist thinker subagents
- `/claudity:message` builds the project narrative and audience-specific messaging

Or just talk: with the plugin enabled, Claude engages Claudity's router skill when
you want to explore what to build, clarify requirements, brainstorm risks, or
make a consequential choice.

## Cost and privacy

The plugin adds about 800 tokens of always-on context per session. Process
guides load on demand when a phase starts (roughly 2k to 8k tokens each), and
the failure-brainstorming thinkers run as subagents, which is the main token
spend; quick mode keeps them bounded. As a reference point, the
[example session](docs/example-session.md) cost about $2.80 on the largest
model over three substantial turns.

Everything Claudity produces is plain files in your repo. Your conversation
goes through Claude Code to Anthropic exactly like any other session; the
plugin makes no other network calls and collects no telemetry.

## Uninstall

- Plugin: `/plugin uninstall claudity`
- Per project: delete `.clarity-protocol/` and remove the block between
  `<!-- claudity-begin -->` and `<!-- claudity-end -->` in `CLAUDE.md`

## What comes out

```text
.clarity-protocol/
├── summary.md                  # what this project is, for a general audience
├── notes.md                    # shared memory: principles, cross-phase observations
├── observations.md             # patterns and coverage notes from analysis
├── goal/
│   ├── problem.md              # what you're trying to achieve and why
│   ├── stakeholders.md         # who cares about the outcome
│   ├── requirements.md         # criteria any solution must satisfy
│   ├── open-questions.md       # unknowns that could change the approach
│   └── resolved-questions.md   # answered questions, with findings
├── solution/
│   ├── solution.md             # what you plan to build
│   ├── architecture.md         # how you plan to build it (with threat model)
│   └── solution-summary.md     # concise overview for stakeholders
├── failures/                   # failure modes, chains, management plans
│   └── pool/                   # raw brainstormed failures awaiting analysis
├── decisions/                  # decision log with criteria and rationale
└── config.json                 # dependency graph + content hashes (staleness tracking)
```

Documents form a dependency graph (problem → stakeholders → requirements →
solution → failures/architecture). When an upstream document changes, Claudity
knows what downstream needs revisiting.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/pytest tests/ -q      # free, deterministic
tests/e2e/run.sh                      # headless behavioral smoke (~$2.50, mixed model floors)
```

See [TESTING.md](TESTING.md) for the full test-tier breakdown and cost model,
and [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute (including adding
a new thinker).

Vendored content is pinned to an upstream commit. See [UPSTREAM.md](UPSTREAM.md)
for the vendoring map and re-sync procedure, and [PORTING.md](PORTING.md) for
the substitution rules.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) (portions
Copyright (c) Microsoft Corporation).
