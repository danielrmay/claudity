#!/usr/bin/env bash
# Asserts: architecture-design produced a real architecture doc with the
# Mermaid threat model, the system-design.json sidecar, and recorded state.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

grep -q 'To be determined' "$P/solution/architecture.md" \
  && { fail "architecture.md still template"; exit 1; }
[[ $(wc -c < "$P/solution/architecture.md") -gt 500 ]] || fail "architecture.md suspiciously small" || exit 1
grep -q '```mermaid' "$P/solution/architecture.md" \
  || fail "architecture.md missing the Mermaid threat-model block" || exit 1

python3 -c "import json; json.load(open('$P/system-design.json'))" 2>/dev/null \
  || fail "system-design.json missing or not valid JSON" || exit 1

packet_json "$PROJ" | python3 -c '
import json, sys
report = json.load(sys.stdin)
status = report["documents"]["solution/architecture.md"]["status"]
assert status in ("current", "stale"), f"architecture status: {status}"
' || { fail "architecture.md not recorded"; exit 1; }
exit 0
