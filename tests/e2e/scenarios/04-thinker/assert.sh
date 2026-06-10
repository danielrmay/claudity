#!/usr/bin/env bash
# Asserts: the thinker subagent ran and its findings landed in the pool in
# the documented format, flipping the status engine to recommend
# failure-analysis.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
POOL="$PROJ/.clarity-protocol/failures/pool"

count=$(find "$POOL" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
[[ "$count" -ge 1 ]] || fail "no pool files created" || exit 1

grep -rq 'general-thinker' "$POOL" --include='*.md' \
  || fail "no pool file attributes Source: general-thinker" || exit 1

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
phases = {p["process"]: p["status"] for p in report["processAvailability"]}
assert phases.get("failure-analysis") == "recommended", phases
' || { fail "status engine does not recommend failure-analysis after pooling"; exit 1; }
exit 0
