#!/usr/bin/env bash
# Claudity Tier 2 e2e smoke suite — headless claude runs with deterministic
# artifact assertions and a hard cost budget.
#
# Usage:
#   e2e/run.sh           # all scenarios
#   e2e/run.sh 01        # scenarios matching a prefix
#
# Env:
#   CLAUDITY_TEST_MODEL    model for runs (default: haiku)
#   CLAUDITY_MAX_COST_USD  fail if total cost exceeds this (default: 1.50)
#   CLAUDITY_SKIP_THINKER  =1 to skip the (most expensive) thinker scenario
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

FILTER="${1:-}"
MAX_COST="${CLAUDITY_MAX_COST_USD:-1.50}"
declare -a NAMES RESULTS COSTS PROJECTS
overall=0

# Scratch dirs are removed when the suite passes; kept (with paths printed)
# on failure or when CLAUDITY_E2E_KEEP=1, for debugging.
cleanup() {
  if [[ "$overall" == "0" && "${CLAUDITY_E2E_KEEP:-0}" != "1" ]]; then
    rm -rf "$ART_DIR" "${PROJECTS[@]:-}" 2>/dev/null
  else
    echo "kept artifacts: $ART_DIR"
    printf 'kept project: %s\n' ${PROJECTS[@]+"${PROJECTS[@]}"}
  fi
}
trap cleanup EXIT

echo "Claudity e2e — model: $MODEL, artifacts: $ART_DIR"
echo

for scenario in "$HERE"/scenarios/*/; do
  name="$(basename "$scenario")"
  [[ -n "$FILTER" && "$name" != "$FILTER"* ]] && continue
  if [[ "$name" == *thinker* && "${CLAUDITY_SKIP_THINKER:-0}" == "1" ]]; then
    echo "── $name: SKIPPED (CLAUDITY_SKIP_THINKER=1)"
    continue
  fi

  # Scenario config: FIXTURE (empty|with-fixture), MAX_TURNS
  FIXTURE="empty"; MAX_TURNS=25
  # shellcheck source=/dev/null
  source "$scenario/config.sh"

  echo "── $name (fixture: $FIXTURE, max turns: $MAX_TURNS)"
  proj="$(new_project "$FIXTURE")"
  PROJECTS+=("$proj")
  out="$ART_DIR/$name.json"
  run_claude "$proj" "$scenario/prompt.md" "$MAX_TURNS" "$out"

  if bash "$scenario/assert.sh" "$proj" "$out" "$REPO"; then
    status="PASS"
  else
    status="FAIL"; overall=1
    echo "    project: $proj"
    echo "    result:  $out"
  fi
  cost="$(json_field "$out" total_cost_usd)"
  [[ -z "$cost" ]] && cost=0
  NAMES+=("$name"); RESULTS+=("$status"); COSTS+=("$cost")
  echo "    $status (\$$cost)"
done

echo
echo "scenario                 result   cost_usd"
echo "------------------------ ------   --------"
total=0
for i in ${NAMES[@]+"${!NAMES[@]}"}; do
  printf "%-24s %-6s   %s\n" "${NAMES[$i]}" "${RESULTS[$i]}" "${COSTS[$i]}"
  total=$(python3 -c "print(round($total + ${COSTS[$i]}, 4))")
done
echo "------------------------ ------   --------"
printf "%-24s %-6s   %s (budget: %s)\n" "total" "" "$total" "$MAX_COST"

if python3 -c "import sys; sys.exit(0 if $total > $MAX_COST else 1)"; then
  echo "BUDGET EXCEEDED: \$$total > \$$MAX_COST" >&2
  overall=1
fi

exit "$overall"
