#!/usr/bin/env bash
# Asserts: failure-analysis consumed the mailbox (snapshot to archive),
# produced analyzed failure files and a real index, and recorded state.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

leftover=$(find "$P/mailboxes/failure-brainstorm" -maxdepth 1 -name '[0-9]*.md' 2>/dev/null | wc -l | tr -d ' ')
[[ "$leftover" == "0" ]] || fail "$leftover mailbox item(s) not consumed/snapshotted" || exit 1

# The fixture ships one already-consumed snapshot (20260609-000000); the
# three seeds must land in a NEW snapshot directory.
archived=$(find "$P/archive/failure-brainstorm" -path '*snapshot-*' -name '*.md' \
  ! -path '*snapshot-20260609-000000*' 2>/dev/null | wc -l | tr -d ' ')
[[ "$archived" -ge 3 ]] || fail "expected >=3 newly archived seeds, found $archived" || exit 1

grep -q 'No failure modes have been analyzed yet' "$P/failures/failures.md" \
  && { fail "failures.md still template"; exit 1; }

new_failures=$(ls "$P"/failures/failure-0*.md 2>/dev/null | grep -vc 'failure-01-token-replay' | tr -d ' ')
[[ "$new_failures" -ge 1 ]] || fail "no new analyzed failure-NN files beyond the fixture's" || exit 1

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
status = report["documents"]["failures/failures.md"]["status"]
assert status in ("current", "stale"), f"failures.md status: {status} (not recorded?)"
' || { fail "failures.md not recorded"; exit 1; }
exit 0
