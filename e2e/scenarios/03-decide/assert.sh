#!/usr/bin/env bash
# Asserts: a numbered decision file with real content exists, the index was
# updated past its template, and decisionState was recorded (R5 discipline)
# with status decided and non-empty relatedDocs.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
P="$PROJ/.clarity-protocol"

decision_file="$(ls "$P"/decisions/decision-0*-*.md 2>/dev/null | head -1)"
[[ -n "$decision_file" ]] || fail "no decisions/decision-NN-*.md created" || exit 1
[[ $(wc -c < "$decision_file") -gt 300 ]] || fail "decision file suspiciously small" || exit 1
grep -qi 'sqlite' "$decision_file" || fail "decision file doesn't mention the chosen option" || exit 1

grep -q 'No decisions have been recorded yet' "$P/decisions/decisions.md" \
  && { fail "decisions.md index still template"; exit 1; }

python3 - "$P/config.json" <<'PYEOF' || exit 1
import json, sys
cfg = json.load(open(sys.argv[1]))
state = cfg.get("decisionState", {})
assert state, "no decisionState in config.json — --record-decision was not run"
entry = next(iter(state.values()))
assert entry.get("status") == "decided", f"status: {entry.get('status')}"
assert entry.get("relatedDocs"), "relatedDocs empty — decision not grounded"
PYEOF
exit 0
