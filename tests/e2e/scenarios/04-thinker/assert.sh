#!/usr/bin/env bash
# Asserts: the thinker subagent ran and its findings were recorded into the
# failure-brainstorm mailbox with provenance, flipping the status engine to
# recommend failure-analysis.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
BOX="$PROJ/.clarity-protocol/mailboxes/failure-brainstorm"

count=$(find "$BOX" -maxdepth 1 -name '[0-9]*.md' 2>/dev/null | wc -l | tr -d ' ')
[[ "$count" -ge 1 ]] || fail "no mailbox items created" || exit 1

grep -rq 'general-thinker' "$BOX" --include='*.md' \
  || fail "no mailbox item attributes Source: general-thinker" || exit 1

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
phases = {p["process"]: p["status"] for p in report["processAvailability"]}
assert phases.get("failure-analysis") == "recommended", phases
' || { fail "status engine does not recommend failure-analysis after recording"; exit 1; }
exit 0
