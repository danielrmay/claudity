# Failure Modes

Failures are organized by severity and impact. See [failure-taxonomy.md](failure-taxonomy.md) for complete taxonomy with severity calls and mitigation priorities.

## Identified Failures

1. **[Token Replay After Logout](failure-01-token-replay.md)** (HIGH) 
   - Revoked session tokens remain valid in edge cache, allowing attackers to reuse stolen tokens and modify feature flags
   - Mitigation: 60s cache TTL (short-term), revocation list with push-based cache invalidation (long-term)
   - Related: Logout race condition, session fixation (if cookies used)

## Cross-Cutting Patterns

**Authentication & Session Management failures** — Token replay, logout races, session fixation all share a common root: cache/propagation lag on revocation. Architectural decision on auth mechanism (cookies vs. tokens) and cache invalidation strategy will address multiple failures simultaneously.

**CRITICAL failures** (unauditable modifications) require immediate blocking before MVP. **HIGH failures** (privilege escalation with audit trail) are in-scope for current sprint. See [failure-taxonomy.md](failure-taxonomy.md) for priority order.
