#!/usr/bin/env bash
# Add an analyzed failure without a management plan; its placeholder text
# matches protocol_status.py's _MGMT_PLACEHOLDER_PATTERNS, so the status
# engine recommends failure-management.
set -euo pipefail
PROJ="$1"
cat > "$PROJ/.clarity-protocol/failures/failure-02-snapshot-poisoning.md" <<'EOF'
# Failure 02: Snapshot poisoning via shared store

## Failure Chain

1. Attacker gains write access to the shared snapshot store
2. Replaces a popular named snapshot with one containing malicious rows
3. Teammates restore it locally; poisoned data flows into bug reports and test fixtures
4. Harm: corrupted local environments across the team, loss of trust in shared snapshots

## Management Plan

[Not yet developed — Run failure management]
EOF

# A coherent post-analysis packet: the index lists analyzed failures (in real
# flows failure-NN files only exist once analysis has written the index).
cat > "$PROJ/.clarity-protocol/failures/failures.md" <<'EOF'
# Failure Modes

| # | Failure | Severity | Management |
| - | ------- | -------- | ---------- |
| [01](failure-01-token-replay.md) | Token replay after logout | high | planned |
| [02](failure-02-snapshot-poisoning.md) | Snapshot poisoning via shared store | high | not yet developed |
EOF
