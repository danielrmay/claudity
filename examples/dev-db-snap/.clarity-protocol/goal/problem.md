# Problem Statement

When a dev team member hits a bug that depends on specific database state, sharing that state with a colleague is currently painful and often fails: the team takes screenshots of rows and pastes SQL into Slack, and reproducing the exact state takes an afternoon at best. Last week a teammate spent two days on a bug that could have been reproduced instantly if her exact DB state could be shared.

The team needs a way to push and pull named database snapshots between teammates — `snap push bug-1234` / `snap pull bug-1234` — so that reproducing a colleague's exact database state takes two minutes, not two days.

**Framing note:** The goal is fast bug reproduction across the team. The CLI tool is the vehicle for that goal, not the goal itself. This distinction was examined and confirmed — alternative routes (shared staging DB, logical replication) were considered and the tool approach was accepted as the right vehicle.

A Makefile around pg_dump does not solve the problem: the real pain is coordination — who has which dump, where it lives, credential management, and the friction of naming and finding a specific snapshot. A purpose-built tool needs to handle all of that.

## Why This Matters

Bug reproduction time is the bottleneck. A two-day investigation last week was caused entirely by the inability to share DB state cheaply. Multiplied across a team of six, this is a significant and recurring tax on debugging productivity.

## Scope

**In scope:**
- Pushing and pulling named Postgres snapshots between teammates
- Handling the coordination layer: snapshot discovery, naming, credentials, versioning
- Postgres running in Docker only
- Team of six developers

**Out of scope:**
- Non-Postgres databases
- Non-Docker Postgres setups
- Production database management (these are local dev databases)

## Success Criteria

- A teammate can push a named snapshot and another can pull it in under two minutes
- No manual credential sharing or "where did you put the dump" coordination
- Works with Postgres running in Docker
- Works for a team of six without requiring infrastructure expertise to operate
- Data in the snapshot store is treated as production-derived (may contain real user data) — the store must be appropriately secured
