# Stakeholders

## Dev Team (6 engineers)

**Type:** aligned
**Engagement:** direct

**Characteristics:** Small engineering team, mostly seed data but sometimes imports production tables for debugging. Mixed technical levels assumed.

**Goals:** Reproduce colleagues' bug states instantly. Push their own broken/interesting state for others to pull. Spend debugging time on the bug, not on recreating database state.

**Concerns:** Setup friction — if it requires non-trivial configuration it won't get adopted. Accidental data loss (pull overwrites their local DB). Accidentally sharing a snapshot that contains more sensitive data than intended.

## Tool Maintainer (likely the person building it)

**Type:** aligned
**Engagement:** direct

**Characteristics:** The builder. Responsible for keeping it working as the team grows or Docker/Postgres versions change.

**Goals:** Simple codebase that doesn't need constant maintenance. Clear failure modes so teammates can self-serve when something goes wrong.

**Concerns:** Becomes the on-call person for "snap isn't working" if the tool is opaque.

## Adversarial: Data Exfiltration

**Type:** adversarial
**Engagement:** indirect

**Characteristics:** Snapshot store holds production-derived data. An attacker with access to the store (or who intercepts a snapshot in transit) could extract real user data.

**Goals:** Access production-derived data from the snapshot store.

**Concerns (for the builder):** Store access controls, encryption at rest/in transit, and whether snapshot contents are ever logged or exposed in error messages.
