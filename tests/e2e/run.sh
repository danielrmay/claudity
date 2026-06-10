#!/usr/bin/env bash
# Claudity Tier 2 e2e smoke suite — headless claude runs with deterministic
# artifact assertions and a hard cost budget.
#
# Usage:
#   tests/e2e/run.sh                    # all scenarios, sequential
#   tests/e2e/run.sh 01                 # scenarios matching a prefix
#   tests/e2e/run.sh --parallel         # all scenarios concurrently (independent scratch projects)
#   tests/e2e/run.sh --stress 07 6      # 6 parallel copies of one scenario; reports pass rate
#
# Env:
#   CLAUDITY_TEST_MODEL    model for runs (default: haiku)
#   CLAUDITY_MAX_COST_USD  fail if total cost exceeds this (default: 3.00; per process)
#   CLAUDITY_SKIP_THINKER  =1 to skip the (most expensive) thinker scenario
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

# Sessions run against a frozen snapshot of the plugin, never the repo
# (created once per suite; fanout children inherit it). The creator verifies
# snapshot integrity at exit — any session write into the plugin fails the run.
ensure_plugin_snapshot
REPO_STATUS_BEFORE="$(git -C "$REPO" status --porcelain 2>/dev/null)"

# finish <rc> — integrity-check and clean up the snapshot, then exit.
finish() {
  local rc="$1"
  if ! verify_plugin_snapshot; then
    rc=1
  fi
  overall="$rc"  # keep the EXIT-trap cleanup in sync (retains artifacts on failure)
  if [[ "$rc" == "0" && "${CLAUDITY_E2E_KEEP:-0}" != "1" ]]; then
    remove_plugin_snapshot
  elif [[ "${PLUGIN_SNAPSHOT_OWNED:-0}" == "1" ]]; then
    echo "kept plugin snapshot: $PLUGIN_DIR"
  fi
  exit "$rc"
}

# Fan-out helpers: scenarios use isolated scratch projects, so concurrent
# runs are safe. Each job is a child invocation of this script.
fanout() {  # fanout <label:args>... — runs each as a parallel child, reports
  local jobs=("$@") logs=() pids=() failures=0
  for job in "${jobs[@]}"; do
    local log; log=$(mktemp /tmp/claudity-e2e-fan.XXXXXX)
    logs+=("$log")
    # shellcheck disable=SC2086
    CLAUDITY_E2E_KEEP="${CLAUDITY_E2E_KEEP:-0}" "$0" ${job#*:} > "$log" 2>&1 &
    pids+=($!)
  done
  for i in "${!pids[@]}"; do
    wait "${pids[$i]}"; local rc=$?
    local label="${jobs[$i]%%:*}"
    if [[ $rc -eq 0 ]]; then echo "  $label: PASS"; else
      failures=$((failures + 1)); echo "  $label: FAIL (rc=$rc)"
      grep -E 'ASSERT FAIL|kept project|kept artifacts' "${logs[$i]}" | sed 's/^/      /'
    fi
    rm -f "${logs[$i]}"
  done
  echo "fanout: $((${#jobs[@]} - failures))/${#jobs[@]} passed"
  return "$failures"
}

if [[ "${1:-}" == "--stress" ]]; then
  SCEN="${2:?--stress needs a scenario prefix}"; N="${3:-5}"
  jobs=(); for i in $(seq 1 "$N"); do jobs+=("$SCEN#$i:$SCEN"); done
  echo "stress: $N parallel runs of $SCEN (model: $MODEL)"
  fanout "${jobs[@]}"; finish $?
fi

if [[ "${1:-}" == "--parallel" ]]; then
  jobs=()
  for scenario in "$HERE"/scenarios/*/; do
    name="$(basename "$scenario")"
    [[ "$name" == *thinker* && "${CLAUDITY_SKIP_THINKER:-0}" == "1" ]] && continue
    jobs+=("$name:$name")
  done
  echo "parallel suite: ${#jobs[@]} scenarios (model: $MODEL)"
  fanout "${jobs[@]}"; finish $?
fi

FILTER="${1:-}"
MAX_COST="${CLAUDITY_MAX_COST_USD:-3.00}"
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

  # Scenario config: FIXTURE (empty|with-fixture), MAX_TURNS,
  # optional MODEL_FLOOR (ambient conversational flows need Sonnet-class
  # models; CLAUDITY_TEST_MODEL still overrides when explicitly set).
  FIXTURE="empty"; MAX_TURNS=25; MODEL_FLOOR=""
  # shellcheck source=/dev/null
  source "$scenario/config.sh"
  SCENARIO_MODEL="$MODEL"
  if [[ -n "$MODEL_FLOOR" && -z "${CLAUDITY_TEST_MODEL:-}" ]]; then
    SCENARIO_MODEL="$MODEL_FLOOR"
  fi
  export SCENARIO_MODEL

  echo "── $name (fixture: $FIXTURE, max turns: $MAX_TURNS, model: $SCENARIO_MODEL)"
  proj="$(new_project "$FIXTURE")"
  PROJECTS+=("$proj")
  # Optional per-scenario state mutation (e.g. blank a doc, seed pool files).
  if [[ -f "$scenario/setup.sh" ]]; then
    bash "$scenario/setup.sh" "$proj" "$REPO" || { echo "    setup.sh failed"; overall=1; continue; }
  fi
  out="$ART_DIR/$name.json"
  run_conversation "$proj" "$scenario" "$MAX_TURNS" "$out"

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

# Defense in depth: sessions only ever see the snapshot, so the real repo
# should be untouched — flag any NEW drift (relative to suite start, so
# developer work-in-progress doesn't false-positive). Drift here would
# indicate the snapshot indirection leaked.
if [[ "$(git -C "$REPO" status --porcelain 2>/dev/null)" != "$REPO_STATUS_BEFORE" ]]; then
  echo "WARNING: the repo's git status changed during this run; a session may have strayed into the repo" >&2
fi

finish "$overall"
