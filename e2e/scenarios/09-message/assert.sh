#!/usr/bin/env bash
# Asserts: message-clarification produced a real general-audience summary and
# recorded it.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

grep -q 'Write this like' "$P/summary.md" && { fail "summary.md still template"; exit 1; }
grep -q '\[Project Title\]' "$P/summary.md" && { fail "summary.md still has placeholder title"; exit 1; }
[[ $(wc -c < "$P/summary.md") -gt 300 ]] || fail "summary.md suspiciously small" || exit 1

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
status = report["documents"]["summary.md"]["status"]
assert status in ("current", "stale"), f"summary.md status: {status} (not recorded?)"
' || { fail "summary.md not recorded"; exit 1; }
exit 0
