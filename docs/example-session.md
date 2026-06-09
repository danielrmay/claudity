# Example session

A real first session with Claudity, abridged. This is not a dramatization:
it was produced by running the plugin headlessly (Claude Code, model Fable 5)
against an empty project, with the user's replies scripted between turns.
Cuts are marked with `[...]`; the dialogue is otherwise verbatim. The files
shown at the end are what the session actually wrote.

---

**You:**

> I want to build a CLI tool that snapshots and restores local dev databases.
> Can you help me think it through with claudity before I start coding?

**Claudity:**

> So: a CLI that snapshots and restores local dev databases. I can already
> imagine the tool — but I want to make sure I understand the *pain* first,
> because "a snapshot CLI" is an artifact, and the goal is presumably some
> state of the world like "getting my dev database back to a known-good state
> is a 5-second non-event instead of a 20-minute chore."
>
> A few questions to start — answer in whatever order feels natural:
>
> 1. **What happens today when your dev DB gets into a bad state?** Walk me
>    through the actual sequence [...] roughly how often does this happen and
>    how long does it take?
> 2. **What prompted this now?** Was there a specific incident [...]?
> 3. **The magic-wand test:** if snapshot/restore already existed and worked
>    perfectly, what would you actually do differently day-to-day?
> 4. **Who's it for?** Just you, your team, or are you thinking public OSS
>    tool? And which database engines are actually in your daily life?
>
> One honest check worth doing early: depending on your answers, the right
> solution might turn out to be smaller than a tool — e.g. a Makefile around
> `pg_dump`. If it survives that comparison, great — then we know exactly
> what the tool adds.

**You:**

> Today: when someone hits a weird bug state we screenshot rows and paste SQL
> in Slack, and reproducing it takes an afternoon if it works at all. What
> prompted it: last week a teammate spent two days on a bug I could have
> reproduced instantly with her exact DB. Magic wand: a teammate says
> `snap push bug-1234`, I say `snap pull bug-1234`, and I am looking at her
> exact data two minutes later. It's for my team of six, Postgres in Docker
> only. And to your honest check: a Makefile around pg_dump doesn't solve the
> sharing part — credentials, where dumps live, who has which version — that
> coordination is the actual pain.

**Claudity:**

> Here's the thing your answer surfaced, and I want to say it explicitly
> rather than quietly absorb it: **you're not building a snapshot tool —
> you're building a state-sharing tool.** "Snapshot and restore local dev
> databases" was the framing you walked in with, but every detail you just
> gave — push/pull, names like `bug-1234`, credentials, "who has which
> version" — describes a *distribution* problem. [...] That matters because
> the hard parts of those two products are completely different: a local
> snapshot tool lives or dies on dump/restore mechanics; a sharing tool lives
> or dies on the shared store, auth, naming, and trust. Does that reframe
> sound right to you?
>
> Assuming it does, it opens four questions I'd want answered before we talk
> solutions, roughly in order of how much they could change the design:
>
> 1. **What's actually *in* these dev databases?** This is the big one. If
>    they're synthetic seed data, the shared store can be a dumb S3 bucket
>    and we move on. But if dev DBs ever contain production-derived rows or
>    real customer data — which is exactly the kind of data that makes a bug
>    "only reproducible with her exact DB" — then `snap push` is quietly
>    building an unaudited archive of customer data, copied to a bucket and
>    six laptops. [...]
> 2. **How big, really?** "Two minutes later" has to cover dump + upload +
>    download + restore. [...]
> 3. **The schema-version trap.** Her `bug-1234` snapshot was taken at
>    migration 0142. You pull it while your checked-out branch expects
>    migration 0145. Now you have her exact data and code that can't read
>    it — or worse, code that *almost* can. [...]
> 4. **Who runs the store?** [...] it has to solve that problem, not relocate
>    it to you as the person who hands out bucket keys.
>
> And one smaller thing worth a sentence: when I `snap pull bug-1234`, what
> happens to *my* current local data? Gone, replaced silently? [...] it may
> just mean pull auto-snapshots whatever it's about to overwrite.

**You:**

> Yes, the state-sharing reframe is right. Mostly seed data but we do
> sometimes import a prod table — point taken. Let's stop here for today;
> capture where we got to and tell me where we'd pick up next time.

**Claudity:**

> Everything's saved. Here's where we landed and where we pick up.
>
> **What today established:**
>
> 1. **The reframe, confirmed:** this is a *team state-sharing* tool, not a
>    local snapshot tool. [...] This is now the recorded framing, with your
>    rejection of "Makefile around pg_dump" preserved as the reasoning.
> 2. **The success bar:** a state-dependent bug handed to a teammate in
>    ~2 minutes end-to-end, first try, no Slack archaeology.
> 3. **The constraint that will shape requirements:** dev DBs sometimes
>    contain imported production tables, so the shared store will hold
>    production-derived data. That's now a confirmed indirect stakeholder
>    (people whose data is in those tables), not a hypothetical.
>
> **Where we pick up next time** — five open questions, all answerable in
> conversation, roughly in order of design impact: [DB size; schema-version
> coupling; who runs the store; pull semantics; prod-data handling]
>
> Answer those and the requirements basically write themselves [...] Just run
> `/claudity:start` next time — it'll read the state and pick up at the
> requirements conversation.

---

## What was written to disk

Three documents reached "current" during this one conversation; nothing was
held only in chat:

```text
  ✓ goal/problem.md                     current
  ✓ goal/stakeholders.md                current
  ○ goal/requirements.md                empty
  ✓ goal/open-questions.md              current
  ○ solution/solution.md                empty
  ...
```

From the `goal/problem.md` it wrote (excerpt):

> **Confirmed framing (2026-06-09):** this is a *team state-sharing* tool,
> not a local snapshot tool. The user originally framed it as "a CLI that
> snapshots and restores local dev databases," but the real pain is
> coordination — credentials, where dumps live, who has which version. [...]
> A "Makefile around pg_dump" was explicitly rejected because it doesn't
> solve the sharing part.

The stakeholder map it recorded includes the six developers, the maintainer,
the production-data subjects, and an adversarial "whoever obtains the store's
contents" — which is the seed for the failure-brainstorming phase later.

Session cost: about $2.80 on Fable 5 across three turns (smaller models work
too and cost proportionally less; the questioning is sharpest on frontier
models).
