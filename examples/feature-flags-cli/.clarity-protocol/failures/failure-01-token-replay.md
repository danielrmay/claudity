# Failure 01: Token replay

## Failure Chain

1. logout -> 2. cache -> 3. takeover

## Management Plan

Short-term: cache TTL 60s. Long-term: revocation push.
