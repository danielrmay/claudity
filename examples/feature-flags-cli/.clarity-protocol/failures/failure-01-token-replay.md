# Failure: Token Replay After Logout

## Summary

A user logs out and their session token is revoked, but the edge cache continues to accept that token for up to its TTL. An attacker who obtained the token before logout can still authenticate and modify feature flags, compromising the integrity of the platform. This affects platform engineers and product managers who may be unaware their account has been compromised after logout.

## Failure Chain

1. User (legitimate) authenticates and receives a session token. Token is cached at edge.

2. Attacker obtains the token (e.g., stolen from logs, intercepted network traffic, compromised device).

3. User initiates logout. Logout request reaches the auth service and the token is revoked.
   - *Intervention point (Prevention):* Implement immediate token revocation that propagates to all cache layers, not just central auth.

4. Revocation is recorded in the auth service, but the edge cache has not yet been invalidated.
   - *Observation:* With distributed caching, revocation may propagate asynchronously or not at all if push-based invalidation is not implemented.
   - *Intervention point (Detection):* Log all token validations to detect unexpected use patterns post-logout.

5. Attacker (still holding the pre-logout token) makes a request to the API. **harm begins**
   - *Intervention point (Detection):* Cross-reference token timestamps against revocation events.

6. The edge cache validates the token against its cached state and accepts it (token is still within its cache TTL).

7. Request reaches the API server with the attacker's authenticated credentials.
   - *Intervention point (Mitigation):* Require backend re-validation of tokens against a revocation list, even if cached.

8. API server processes the request as the legitimate user and allows feature flag modifications.
   - *Observation:* The attacker now has full privileges of the compromised account. For a feature-flag system, this means unauthorized flag changes, feature rollbacks, or strategic flag deployments.

9. Malicious flag changes propagate to systems depending on those flags. **harm continues**

10. User may not be aware of the compromise. Harm detection relies on monitoring (anomalous flag changes, audit logs reviewed by operators).
    - *Intervention point (Detection):* Real-time alerting on unexpected flag changes, especially out-of-business-hours or from new IPs.
    - *Observation:* "Unexpected" is context-dependent and hard to define for a feature-flag system. Not all flag changes are obviously malicious.

11. Once detected, operators revoke the account, audit logs, and remediate modified flags. **harm ends**

## Observations

- **Severity:** High — Unauthorized privilege escalation with full account compromise. For a feature-flag system controlling production behavior, impact is direct and platform-wide.
- **Related failures:** Token theft (prerequisite), logout race conditions (concurrent logout while attacker requests), cache inconsistency (more general case of revocation not propagating).
- **Variants:** Pre-logout token theft (stolen token used before logout); token cached across multiple geographies (revocation only propagates to one region).

## Intervention Points

### Prevention
- Immediate revocation with synchronous propagation to edge caches (not just async invalidation)
- Implement cache-aside pattern with revocation list: always check backend for revoked tokens on critical operations
- Minimize token cache TTL to reduce the window of vulnerability (60s as short-term mitigation)

### Detection
- Log all token validations and flag all post-logout token use
- Real-time alerting on unexpected flag modifications (anomaly detection based on user patterns, time-of-day, IP)
- Audit every flag change with user, timestamp, and IP address

### Mitigation
- Require backend re-validation of tokens for sensitive operations (flag changes, account modifications)
- Implement staged rollout of flag changes to reduce blast radius of malicious modifications
- Implement flag change approval workflows for critical flags

### Recovery
- Revoke compromised account and all issued tokens
- Audit logs to identify the window of compromise
- Remediate unauthorized flag changes (rollback or manual correction)
- Notify affected users of the security incident

---

## Management Plan

**Short-term (immediate):** Reduce edge cache TTL from default to 60 seconds. This limits the window of vulnerability after logout to 60s, acceptable for the <1min flag flip requirement.

**Long-term (next phase):** Implement revocation list with push-based cache invalidation. When a token is revoked, push invalidation to all edge cache layers immediately. Requires coordination with infrastructure team on cache layer capabilities.
