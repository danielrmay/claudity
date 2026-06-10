#!/usr/bin/env bash
# Seed the failure-brainstorm mailbox with three raw failures via the
# vendored recording CLI (same code path as the record_failure MCP tool).
set -euo pipefail
PROJ="$1"
REPO="$2"
cd "$PROJ"

python3 "$REPO/scripts/brainstorm.py" record-failure <<'EOF'
{
  "title": "Silent flag drift between environments",
  "source": "broad-analysis",
  "description": "The CLI's local cache and the flags service disagree after a network partition; engineers act on stale flag state and ship a feature dark that they believe is live."
}
EOF

python3 "$REPO/scripts/brainstorm.py" record-failure <<'EOF'
{
  "title": "Audit log gap under concurrent flips",
  "source": "broad-analysis",
  "description": "Two operators flip the same flag within a second; only one write lands in the audit log, breaking the compliance requirement that every flip is attributable."
}
EOF

python3 "$REPO/scripts/brainstorm.py" record-failure <<'EOF'
{
  "title": "Service token scope creep",
  "source": "security-thinker",
  "pre_existing": false,
  "description": "The CLI's service token, issued for flag reads, also authorizes writes; a leaked developer laptop token lets an attacker flip production flags.",
  "failure_chain": [
    {"step_number": 1, "description": "token issued over-scoped"},
    {"step_number": 2, "description": "laptop compromised"},
    {"step_number": 3, "description": "attacker flips kill-switch flag", "harm_begins": true},
    {"step_number": 4, "description": "production outage"}
  ]
}
EOF
