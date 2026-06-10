# Decision: SQLite vs Postgres for flag state storage

**Date:** 2026-06-09  
**Decided by:** Daniel May  
**Status:** Decided

## Question

Should the Claudity CLI store feature-flag state in SQLite (embedded, file-based) or Postgres (client-server)?

## Context & Assumptions

- **Deployment model:** Single-node
- **User base:** One operator
- **Write volume:** Low
- **Priority:** Simplicity over scalability
- **Team expertise:** Comfortable with SQL either way

## Options

### SQLite
- Zero setup — runs embedded in the CLI process
- File-based storage — portable, easy to snapshot and backup
- No external dependencies or server process
- Single writer at a time (concurrency limitation is irrelevant at low write volume)
- **Fits the stated constraints perfectly**

### Postgres
- Would support future scaling to multi-operator or multi-node deployments
- Requires running a separate server process
- Adds network calls and connection pooling complexity
- Higher operational burden — installation, management, cloud hosting
- **Overkill for single-operator, low-volume workload**

## Decision

**Use SQLite.**

The stated constraints (single-operator, low write volume, simplicity prioritized) align completely with SQLite's strengths and make Postgres's benefits irrelevant. SQLite provides everything needed without the operational friction of a separate database server.

## Reasoning

Postgres buys future scalability options (multi-operator, distributed access) that you don't currently need. The cost is operational complexity — managing a separate service, coordinating its deployment, handling backups, and adding network overhead to every CLI call. For a single-operator tool with stated simplicity priorities, that's a poor tradeoff.

SQLite is the right tool when simplicity is the goal and concurrency pressure is absent. If that context changes (need for multi-operator access, multi-node deployments), migration to Postgres becomes necessary but is a bounded problem.

## Reconsideration Triggers

- Multiple operators need concurrent access to flag state from different machines
- Deployment model shifts to multi-node or service-oriented architecture
- Write volume increases enough to stress single-writer concurrency model

## Related Documents

- (none yet — protocol context TBD)
