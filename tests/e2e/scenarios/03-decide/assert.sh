#!/usr/bin/env bash
# Asserts: a NEW numbered decision file with real content exists (the fixture
# already ships decision-01-go-vs-rust), the index references it, and
# decisionState gained a decided entry with non-empty relatedDocs (R5
# discipline) beyond the fixture's pre-existing one.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

decision_file="$(grep -lir 'sqlite' "$P"/decisions/decision-*.md 2>/dev/null | head -1)"
[[ -n "$decision_file" ]] || fail "no decision file mentioning the chosen option (sqlite)" || exit 1
[[ $(wc -c < "$decision_file") -gt 300 ]] || fail "decision file suspiciously small" || exit 1

grep -qi 'sqlite\|postgres\|storage\|02' "$P/decisions/decisions.md" \
  || fail "decisions.md index not updated for the new decision" || exit 1

python3 - "$P/config.json" <<'PYEOF' || exit 1
import json, sys
cfg = json.load(open(sys.argv[1]))
state = cfg.get("decisionState", {})
new = {k: v for k, v in state.items() if k != "decision-01-go-vs-rust"}
assert new, "no new decisionState entry — --record-decision was not run"
entry = next(iter(new.values()))
assert entry.get("status") == "decided", f"status: {entry.get('status')}"
assert entry.get("relatedDocs"), "relatedDocs empty — decision not grounded"
PYEOF
exit 0
