# Failure Taxonomy & Severity Calls

**Date:** 2026-06-09  
**Status:** Ready for Management Phase

---

## **CRITICAL: Unauditable Flag Modifications**

Core requirement violation (audit log for every flip). Enable untraced sabotage.

1. **Flag modification without auth context**
   - API accepts requests with missing/invalid auth headers; processes flag changes without user attribution
   - *Severity: CRITICAL*

2. **Concurrent flag modifications racing to inconsistent state**
   - Multiple simultaneous changes on same flag result in indeterminate state
   - Audit logs show contradictory records; forensics fail
   - *Severity: CRITICAL*

---

## **HIGH: Privileged Escalation with Delayed Detection**

Complete privilege escalation; audit trail exists but detection is reactive.

1. **Token replay after logout** ✓ [documented: failure-01-token-replay.md]
   - Revoked token still valid in edge cache; attacker modifies flags before revocation propagates
   - Window: 60s–TTL; short-term mitigation (60s TTL) proposed; long-term: revocation list + push invalidation
   - *Severity: HIGH*

2. **Logout race condition**
   - User initiates logout while attacker requests auth simultaneously; request wins race
   - Attacker gets fresh credentials post-logout
   - *Severity: HIGH*

3. **Session fixation in cookie-based auth**
   - If using cookies, attacker can fix session ID before auth, reuse post-logout
   - *Severity: HIGH* (if auth mechanism uses cookies)

---

## **MEDIUM: Privilege Boundary Violations with Audit Trail**

Lower-privilege users affect high-privilege operations; changes are logged.

1. **Flag change approval bypass**
   - User with read-only access queues flag change; approval workflow race allows execution without sign-off
   - *Severity: MEDIUM*

2. **Regional cache desync on revocation**
   - Token revoked in region A, still valid in region B
   - Affects one region; audit logs span regions; TTL-bounded
   - *Severity: MEDIUM*

---

## **LOW: Information Leaks & Availability Issues**

Don't affect flag integrity; impact confidentiality or reliability.

1. **Flag state information disclosure**
   - API leaks flag existence via error messages or timing side-channels
   - *Severity: LOW*

2. **Slow audit log queries under load**
   - Retrieving audit history blocks during incident response
   - *Severity: LOW*

---

## **Mitigation Priority**

1. **CRITICAL** — Block immediately before MVP
2. **HIGH** — Implement in current sprint (token-replay mitigations already proposed)
3. **MEDIUM** — Design into architecture upfront
4. **LOW** — Address post-MVP

---

## **Next Steps: Management Phase**

- Map failures to architectural decisions (cache strategy, auth mechanism, approval workflows)
- Assign owners and timelines
- Define success criteria for each mitigation
- Track through implementation
