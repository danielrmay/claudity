#!/usr/bin/env bash
# Asserts: the model ran the status command and correctly relayed the
# recommended next process for the fixture packet (failures.md is the first
# non-current doc; with an analyzed+managed failure and an empty pool, the
# correct phase is failure-brainstorming).
set -uo pipefail
PROJ="$1"; OUT="$2"; REPO="$3"
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"

text="$(result_text "$OUT")"
line="$(grep -E '^RECOMMENDED:' <<<"$text" | tail -1)"
if [[ -n "$line" ]]; then
  grep -q 'failure-brainstorming' <<<"$line" || fail "expected failure-brainstorming, got: $line" || exit 1
else
  # Small models sometimes drop the strict format line while still relaying
  # the right recommendation — accept correct behavior over correct format.
  grep -q 'failure-brainstorming' <<<"$text" \
    || fail "result doesn't relay failure-brainstorming: $(tail -c 300 <<<"$text")" || exit 1
fi
exit 0
