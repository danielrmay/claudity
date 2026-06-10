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
