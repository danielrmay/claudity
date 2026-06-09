<!-- Vendored from microsoft/clarity-agent@6b32c43 processes/failure-brainstorming.md — modified per PORTING.md rules R1, R6, R7, R9, R11, R14: the harness tool pipeline (record_failure / record_suggestion / recommend_deeper_analysis / read_thinker_guide + async mailbox) is replaced by pool files and parallel thinker subagents -->

# Failure Brainstorming

This process generates raw failure modes through direct analysis, specialist thinker subagents, and human contributions. Raw failures accumulate in a pool until they're ready for analysis and grouping.

## Overview

The goal of failure brainstorming is breadth: come up with as many things as possible that could go wrong. This is the creative, divergent phase — don't filter, don't group, don't worry about duplicates. That's what failure analysis is for.

Brainstorming can happen over time. Multiple runs can contribute, humans can add their own insights, and the pool grows until someone decides it's ready for analysis. This process can be run multiple times, each run adding to the same pool.

## Recording Findings

Raw failures live in the **brainstorming pool**: `.clarity-protocol/failures/pool/`, one markdown file per failure. Create the directory if it doesn't exist. Write each failure **as you identify it** — don't batch them up. File name: `<source>--<slug>.md` (e.g. `broad--silent-sync-data-loss.md`, `security-thinker--token-replay.md`, `human--regulator-history.md`). Format:

```markdown
# <Short title of what goes wrong>

- **Source:** broad-analysis | <thinker-name> | human (<name or role>)
- **Pre-existing:** yes | no   <!-- optional: does this failure exist before/independent of this project? -->

<1-3 sentences: what fails, how, who is harmed>

**Failure chain:** <step> → <step> → <harm>   <!-- optional -->
```

When your analysis reveals gaps or ambiguities in project documents (missing stakeholders, uncaptured requirements), append a note to `.clarity-protocol/notes.md` tagged for the relevant document, e.g. `[for: problem-clarification] Stakeholders list is missing the on-call operators surfaced during failure brainstorming.`

## Specialist Thinkers

Six specialist thinkers are available as subagents, each with its own methodology:

| Thinker | Lens | Prerequisites (required) |
| ------- | ---- | ------------------------ |
| `general-thinker` | Broad first pass: technical, human, social, misuse, cascading | problem |
| `security-thinker` | AuthN/Z, data protection, injection, cryptography, supply chain | problem, stakeholders |
| `human-factors-thinker` | User/operator error, cognitive biases, information loss | problem, solution |
| `adversarial-analysis-thinker` | Who would attack, why, and how | problem |
| `codebase-scanner-thinker` | Scans the actual repository: routes, configs, auth, secrets | problem (and a codebase) |
| `security-catalog-thinker` | Maps OWASP LLM/Agentic Top 10 + STRIDE catalog to components | problem, stakeholders |

To launch thinkers (Step 4):

1. Resolve the plugin root once: `echo "${CLAUDE_PLUGIN_ROOT}"` via Bash. Env vars are **not** expanded inside subagent prompts, so paste the resolved absolute paths literally.
2. Launch each selected thinker via the Agent tool, using the thinker's name as the agent type — **in parallel (one message, multiple Agent calls) when running more than one**. Each prompt must state:
   - the project directory (absolute path) and protocol directory name (`.clarity-protocol/` or `Clarity Protocol/`)
   - the analysis mode: **quick** or **deep**
   - the absolute path to `<plugin-root>/skills/claudity/processes/failure-reasoning-guidelines.md`
   - for `security-catalog-thinker` only: the absolute path to `<plugin-root>/catalogs/security-catalog.csv`
3. Each thinker returns structured `## Failures` / `## Suggestions` / `## Specialist recommendations` blocks. Persist every returned failure as a pool file (format above, Source = the thinker's name), apply suggestions to `notes.md`, and consider any specialist recommendations for the next round.

Check prerequisites before launching: a thinker whose required documents are empty or missing will produce generic output — skip it and tell the user why.

## When to Use This Process

Run this process when:

- Starting failure analysis for the first time (need raw material to analyze)
- The solution or architecture has changed significantly (new failure modes may exist)
- A domain expert wants to contribute failure ideas
- You want a specific analytical perspective (e.g., just security, or just UX)
- Someone thought of a new "what could go wrong" that should be captured

## Inputs Needed

Before starting, you should have at least:

- `.clarity-protocol/goal/problem.md` — To understand what you're trying to achieve
- `.clarity-protocol/goal/stakeholders.md` — To know who could be affected (especially adversarial and indirect stakeholders)

Ideally you also have:

- `.clarity-protocol/solution/solution.md` — What you're building
- `.clarity-protocol/solution/architecture.md` — How it's built

If the solution isn't fleshed out yet, that's okay. Brainstorming on the problem alone can surface important failure modes early. But the more context you have, the more specific the failures will be.

## Process Steps

### Step 1: Read Project Context

Read the available project documents to understand what you're analyzing:

1. Read `.clarity-protocol/goal/problem.md`
2. Read `.clarity-protocol/goal/stakeholders.md`
3. Read `.clarity-protocol/solution/solution.md` (if it exists)
4. Read `.clarity-protocol/solution/architecture.md` (if it exists)
5. Read `failure-reasoning-guidelines.md` (alongside this guide)

Don't skip this step. You need real context to generate meaningful failures. If key documents are missing, note this and work with what's available.

### Step 2: Broad Analysis

Apply the failure reasoning methodology to analyze the system broadly. Think through:

- **System-in-use thinking** — How will real people actually use this? What happens when they're tired, rushed, confused, or malicious?
- **Component interconnects** — Where do components talk to each other? What happens when one fails, is slow, or returns unexpected data?
- **Stakeholder-by-stakeholder review** — For each stakeholder (including adversarial ones), what could go wrong from their perspective?
- **Human and AI fallibility** — Where do humans make mistakes? Where does AI produce wrong or harmful output?
- **Misuse scenarios** — How could this be deliberately abused or weaponized?
- **Cascading failures** — What small problems could snowball into large ones?

As you identify failure modes, **write each one to the pool immediately**. Each failure should:

- End in actual harm (not just a principle violation)
- Have a clear title that describes what goes wrong
- Include enough description to understand the failure without reading the full chain
- Optionally include a failure chain showing the step-by-step progression

### Step 3: Recommend Specialist Analysis

Review your findings and recommend deeper analysis where specialist methodology would add value. Present your recommendations to the user:

> "I've identified [N] potential failure modes in my broad analysis. I recommend deeper analysis in these areas:
>
> - **[Specialist Name]**: [rationale — what this specialist's lens would catch that broad analysis might miss]
>
> Would you like me to apply any of these specialist perspectives? Or would you prefer to explore a specific area first?"

Be selective — only recommend specialists whose domain expertise is clearly relevant to this particular system, and whose prerequisites are met. Quick mode is the default; suggest deep mode when the area is central to the project's risk profile.

### Step 4: Deepen on Request

When the user asks for deeper analysis in specific areas, launch the selected thinker subagents as described under **Specialist Thinkers** — in parallel when running several. While they run, you can continue talking with the user. When each returns, persist its findings to the pool and give the user a one-line summary per thinker.

You can also deepen without a specialist — if the user asks you to explore a particular area (e.g., "what about data privacy?"), do so using your own analytical reasoning and the failure reasoning methodology, writing findings to the pool as `broad-analysis`.

### Step 5: Invite Human Contributions

After your analysis, ask the user:

> "I've identified [N] potential failure modes so far. Based on your experience or domain knowledge, are there others we should consider? Things that might go wrong that automated analysis might miss?"

Human domain experts often know failure modes that general analysis can't discover — organizational dynamics, historical incidents, regulatory subtleties, cultural factors.

If the user contributes failures, help them formulate each one and write it to the pool with Source `human` (or the contributor's name/role if they specify).

### Step 6: Communicate Results and Hand Off

Summarize what was found:

> "I've brainstormed [N] potential failure modes:
>
> **Broad analysis**: [N] failures (e.g., [1-2 highlights])
> **[Specialist area]**: [N] additional failures (e.g., [1-2 highlights])
> [etc.]
>
> These are in the brainstorming pool, ready for analysis. Would you like to:
> - Add any failure modes from your own experience?
> - Explore a specific area more deeply?
> - Move on to failure analysis (grouping and chain development)?
> - Work on something else?"

**Whatever the user chooses, keep the conversation going.** This process doesn't end in silence — it ends by handing off to the next thing:

- If the user wants to add failures -> stay in this process, capture them, and ask again
- If the user wants deeper analysis -> apply the specialist lens and return to this step
- If the user wants failure analysis -> load and follow the **failure-analysis** process guide
- If the user wants to do something else, or isn't sure -> re-enter the claudity skill main loop

After any process completes, the user should never be left wondering what happens next.

## Outputs and Updates

This process creates/updates:

- `.clarity-protocol/failures/pool/*.md` — Individual raw failure mode files
- `.clarity-protocol/notes.md` — Document improvement suggestions, tagged `[for: ...]` (if any)

## Success Indicators

You've completed brainstorming successfully when:

- Multiple perspectives have examined the system (broad + specialist where relevant)
- Each raw failure mode ends in actual harm (not just a principle violation)
- The pool contains enough raw material for meaningful grouping
- The user has had the opportunity to contribute their domain knowledge

## Common Pitfalls

**Pitfall: Filtering too aggressively**

During brainstorming, the goal is breadth. Don't dismiss a potential failure because it seems unlikely — unlikely + severe is still important. Save filtering for analysis.

**Pitfall: Writing too much per failure**

A raw failure mode should be quick to write and quick to read. If you're spending more than a minute on one, you're doing analysis, not brainstorming. Capture the idea and move on.

**Pitfall: Too narrow a perspective**

Make sure you're thinking beyond just technical failures. Consider human factors, social dynamics, misuse, organizational issues, and cascading effects.

**Pitfall: Skipping human input**

Automated analysis works from general domain knowledge. Humans know the specific organizational, cultural, and historical context. Always ask.

**Pitfall: Not recording as you go**

Write each failure to the pool as you identify it — don't try to batch them. This ensures nothing is lost and the user can see progress in real time.

**Pitfall: Launching thinkers serially**

When the user selects several specialists, launch them in one message so they run concurrently. Serial launches multiply the wait for no benefit.

## Next Steps

After brainstorming, run **failure-analysis** to group raw failures into coherent failure modes with full chains and intervention points.

If the pool isn't ready yet (more brainstorming needed), run this process again later with additional perspectives or human input.
