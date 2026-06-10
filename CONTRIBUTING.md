# Contributing

Thanks for considering a contribution. Claudity is a small experimental
project, so the bar is low and the loop is fast.

## Setup and tests

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/pytest tests/ -q      # Tier 1: free, deterministic; runs in CI
tests/e2e/run.sh                      # Tier 2: headless smoke (~$0.25 on Haiku, optional)
```

See [TESTING.md](TESTING.md) for what each tier covers.

## The upstream-first rule

Claudity vendors its process guides and thinkers from
[microsoft/clarity-agent](https://github.com/microsoft/clarity-agent) and
tracks that repo (see [UPSTREAM.md](UPSTREAM.md)). That splits contributions
in two:

- **Improvements to guide content** (better questions, clearer methodology,
  fixed reasoning) belong **upstream**. File them against microsoft/clarity-agent;
  Claudity picks them up at the next re-sync. Landing them only here would be
  overwritten or create permanent divergence.
- **Claudity-specific work** belongs here: orchestration (how guides drive
  Claude Code skills/subagents), commands, the status scripts, tests, docs,
  and **new thinkers or processes that don't exist upstream**.

Any edit to a vendored file must trace to a numbered rule in
[PORTING.md](PORTING.md). If your change needs a new kind of substitution,
add the rule first.

## Adding a new thinker

Thinkers are read-only subagents launched in parallel by the
failure-brainstorming process. Upstream explicitly invites new failure
domains (accessibility, privacy, scalability, data integrity); if your
thinker is domain-general, consider contributing it upstream first and
porting it here. For a Claudity-only thinker:

1. **Create `agents/<name>-thinker.md`.** Use `agents/general-thinker.md` as
   the template. Frontmatter: `name` (must equal the filename stem),
   `description`, and `tools: Read, Grep, Glob` (thinkers never write).
   Original work gets no `Vendored from` header.
2. **Keep the body in three parts:** a `## Your task` preamble (the launching
   prompt provides project dir, protocol dir, mode quick/deep, and any
   resource paths), a `## Metadata` yaml block (`modes`, `prerequisites`
   with required/recommended protocol docs, `tags`), and your methodology.
3. **End with the standard `## Output format`** (the `## Failures` /
   `## Suggestions` / `## Specialist recommendations` block structure, copied
   exactly from an existing thinker). The orchestrator parses this and
   records failures via `record_failure`; your agent only returns text.
4. **Register it** in two places: the Specialist Thinkers table in
   `skills/risks/SKILL.md` (the failure-brainstorming guide) (name, lens, required
   prerequisites), and `EXPECTED_AGENTS` in `tests/test_plugin_structure.py`.
5. **Verify:** `.venv/bin/pytest tests/ -q`, then optionally run the thinker
   for real against `tests/e2e/fixtures/feature-flags-cli` via the
   `tests/tests/e2e/scenarios/04-thinker` pattern.

## Pull requests

- Run the Tier 1 tests; CI runs them too, plus `claude plugin validate`.
- Update `CHANGELOG.md` (Unreleased section) for user-visible changes.
- Versioning and release mechanics are in
  [UPSTREAM.md](UPSTREAM.md#versioning-and-releases). Maintainers handle
  releases; PRs should not bump versions.

## Conduct

Be kind. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
