# Requirements

Any solution must:

## Functional Requirements

1. Push a named snapshot of a local Postgres (Docker) database to a shared store: `snap push <name>`
2. Pull a named snapshot from the shared store and restore it locally: `snap pull <name>`
3. Handle snapshot discovery — teammates can see what snapshots exist without out-of-band communication
4. Manage credentials for the shared store so teammates don't exchange them manually
5. Work with Postgres running in Docker (not bare-metal Postgres)

## Non-Functional Requirements

### Performance
- Push and pull a typical dev database in under two minutes end-to-end

### Security
- Snapshot store must be treated as holding production-derived data
- Access controls on the store: only the team should be able to read/write snapshots
- Encryption in transit (standard for any cloud store)
- Snapshot contents must not appear in logs or error output

### Usability
- Zero coordination required to use a teammate's snapshot once the tool is set up
- Setup for a new team member should not require infrastructure expertise
- Clear error messages when something goes wrong (wrong name, auth failure, etc.)

### Reliability
- A failed pull must not leave the local database in a broken state — either succeed fully or leave it untouched

## Constraints

- Postgres in Docker only (no bare-metal, no other databases)
- Team of six (no multi-tenancy or enterprise-scale requirements)

## Open / Deferred

- Where snapshots are stored (S3, NAS, git LFS, custom backend) — this is the primary open question and will determine much of the implementation. See open-questions.md.
- Restore semantics: replace existing DB vs. create alongside? Behavior when local schema diverges from snapshot?
