#!/usr/bin/env bash
# Asserts: the headless MCP canary — an ambient risk report lands as exactly
# one new failure-brainstorm mailbox item via the record_failure tool.
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
BOX="$PROJ/.clarity-protocol/mailboxes/failure-brainstorm"

count=$(find "$BOX" -maxdepth 1 -name '[0-9]*.md' 2>/dev/null | wc -l | tr -d ' ')
[[ "$count" == "1" ]] || fail "expected exactly 1 mailbox item, found $count" || exit 1

item=$(find "$BOX" -maxdepth 1 -name '[0-9]*.md')
grep -qi 'flip\|queue\|retry\|silent' "$item" \
  || fail "mailbox item does not describe the reported risk" || exit 1

# Tool-written items carry the renderer's Source line.
grep -q '^\*\*Source:\*\*' "$item" || fail "item missing renderer Source line" || exit 1
exit 0
