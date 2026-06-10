#!/usr/bin/env bash
# Asserts: failure-management replaced failure-02's placeholder with a real
# plan, and the status engine no longer recommends failure-management.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
F="$PROJ/.clarity-protocol/failures/failure-02-snapshot-poisoning.md"

[[ -f "$F" ]] || fail "failure-02 file disappeared" || exit 1
for placeholder in "Not yet developed" "Run failure management"; do
  grep -q "$placeholder" "$F" && { fail "failure-02 still has placeholder: $placeholder"; exit 1; }
done
python3 - "$F" <<'PYEOF' || exit 1
import re, sys
text = open(sys.argv[1]).read()
m = re.search(r"^##\s+Management\s+Plan", text, re.MULTILINE)
assert m, "Management Plan header missing"
body = text[m.end():].strip()
assert len(body) > 200, f"management plan suspiciously thin ({len(body)} chars)"
PYEOF

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
phases = {p["process"]: p["status"] for p in report["processAvailability"]}
assert phases.get("failure-management") != "recommended", phases
# Recording must have happened via the status script: failures.md tracked
# (current or stale), never untracked. Two pre-fix sessions hand-invented
# config bookkeeping and this assert would have caught them.
status = report["documents"]["failures/failures.md"]["status"]
assert status in ("current", "stale"), f"failures.md status: {status} (not recorded?)"
' || { fail "status still recommends failure-management, or failures.md not recorded"; exit 1; }
exit 0
