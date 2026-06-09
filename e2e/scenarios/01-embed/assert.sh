#!/usr/bin/env bash
# Asserts: protocol dir scaffolded with all-empty docs; CLAUDE.md snippet
# installed with markers and no unexpanded placeholders.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"

[[ -d "$PROJ/.clarity-protocol" ]] || fail "no .clarity-protocol/ directory" || exit 1
[[ -f "$PROJ/.clarity-protocol/config.json" ]] || fail "no config.json" || exit 1

empty_count=$(packet_json "$PROJ" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["summary"]["empty"]))' 2>/dev/null)
[[ "$empty_count" == "9" ]] || fail "expected 9 empty docs after fresh embed, got '$empty_count'" || exit 1

[[ -f "$PROJ/CLAUDE.md" ]] || fail "no CLAUDE.md written" || exit 1
grep -q 'claudity-begin' "$PROJ/CLAUDE.md" || fail "CLAUDE.md missing claudity-begin marker" || exit 1
grep -q 'claudity-end' "$PROJ/CLAUDE.md" || fail "CLAUDE.md missing claudity-end marker" || exit 1
if grep -q '{{PROTOCOL_DIR_NAME}}' "$PROJ/CLAUDE.md"; then
  fail "CLAUDE.md contains unexpanded {{PROTOCOL_DIR_NAME}}" || exit 1
fi
exit 0
