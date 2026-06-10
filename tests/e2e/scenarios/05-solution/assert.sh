#!/usr/bin/env bash
# Asserts: solution-brainstorming produced real solution + summary documents
# and recorded them (status: current).
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

grep -q 'To be determined' "$P/solution/solution.md" \
  && { fail "solution.md still template"; exit 1; }
[[ $(wc -c < "$P/solution/solution.md") -gt 300 ]] || fail "solution.md suspiciously small" || exit 1
grep -q 'To be determined' "$P/solution/solution-summary.md" \
  && { fail "solution-summary.md still template"; exit 1; }

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
status = report["documents"]["solution/solution.md"]["status"]
assert status == "current", f"solution/solution.md status: {status} (not recorded?)"
' || { fail "solution.md not recorded as current"; exit 1; }
exit 0
