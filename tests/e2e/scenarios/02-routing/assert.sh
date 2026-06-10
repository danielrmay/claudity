#!/usr/bin/env bash
# Asserts: the model ran the status command and relayed a process the status
# engine actually recommends for this packet. The oracle is computed from the
# engine's own output (graph-walk next action + processAvailability
# "recommended" entries), not a hardcoded expectation — for this fixture the
# engine genuinely recommends more than one process.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"

text="$(result_text "$OUT")"
allowed="$(
{
  packet_json "$PROJ"
  echo "---SPLIT---"
  python3 "$REPO/scripts/protocol_status.py" "$PROJ" --next --json 2>/dev/null || true
} | python3 -c '
import json, sys
raw = sys.stdin.read()
report_raw, _, next_raw = raw.partition("---SPLIT---")
r = json.loads(report_raw)
names = {p["process"] for p in r["processAvailability"] if p["status"] == "recommended"}
try:
    action = json.loads(next_raw)
    if action and action.get("process"):
        names.add(action["process"])
except Exception:
    pass
print("\n".join(sorted(names)))
')"
[[ -n "$allowed" ]] || fail "oracle error: engine recommends nothing for this packet" || exit 1

for name in $allowed; do
  if grep -q "$name" <<<"$text"; then exit 0; fi
done
fail "result relays none of the engine's recommendations ($(tr '\n' ' ' <<<"$allowed")): $(tail -c 300 <<<"$text")"
exit 1
