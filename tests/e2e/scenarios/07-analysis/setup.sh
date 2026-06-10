#!/usr/bin/env bash
# Seed the brainstorming pool with three raw failures in the documented format.
set -euo pipefail
PROJ="$1"
POOL="$PROJ/.clarity-protocol/failures/pool"
mkdir -p "$POOL"
cat > "$POOL/broad--silent-flag-drift.md" <<'EOF'
# Silent flag drift between environments

- **Source:** broad-analysis

The CLI's local cache and the flags service disagree after a network partition; engineers act on stale flag state and ship a feature dark that they believe is live.
EOF
cat > "$POOL/broad--audit-log-gap.md" <<'EOF'
# Audit log gap under concurrent flips

- **Source:** broad-analysis

Two operators flip the same flag within a second; only one write lands in the audit log, breaking the compliance requirement that every flip is attributable.
EOF
cat > "$POOL/security-thinker--token-scope-creep.md" <<'EOF'
# Service token scope creep

- **Source:** security-thinker
- **Pre-existing:** no

The CLI's service token, issued for flag reads, also authorizes writes; a leaked developer laptop token lets an attacker flip production flags.

**Failure chain:** token issued over-scoped → laptop compromised → attacker flips kill-switch flag → production outage
EOF
