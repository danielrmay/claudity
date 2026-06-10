#!/usr/bin/env bash
# Shared helpers for Claudity e2e scenarios. Sourced by run.sh.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="${CLAUDITY_TEST_MODEL:-haiku}"
ART_DIR="${CLAUDITY_E2E_ART_DIR:-$(mktemp -d /tmp/claudity-e2e-art.XXXXXX)}"

# new_project [with-fixture] — fresh scratch git project, echoes its path.
new_project() {
  local dir
  dir=$(mktemp -d /tmp/claudity-e2e-proj.XXXXXX)
  mkdir "$dir/.git"
  if [[ "${1:-empty}" == "with-fixture" ]]; then
    cp -R "$REPO/examples/feature-flags-cli/.clarity-protocol" "$dir/.clarity-protocol"
  fi
  echo "$dir"
}

# run_conversation <project_dir> <scenario_dir> <max_turns> <out_json>
# Scripted multi-turn persona: plays each turns/NN.md as a user message in
# one headless session (first via -p, then -p --resume). <out_json> ends up
# holding the LAST turn's result JSON, with scenario-total cost merged in as
# total_cost_usd; per-turn JSON is kept alongside as <out>.turn-N.json.
# Never fails the shell; callers inspect the JSON and artifacts.
run_conversation() {
  local proj="$1" scenario="$2" turns_cap="$3" out="$4"
  local session_id="" n=0 turn_out total=0
  for turn_file in "$scenario"/turns/*.md; do
    n=$((n + 1))
    turn_out="${out%.json}.turn-$n.json"
    (
      cd "$proj" || exit 1
      if [[ -z "$session_id" ]]; then
        claude -p "$(cat "$turn_file")" \
          --plugin-dir "$REPO" --model "${SCENARIO_MODEL:-$MODEL}" --max-turns "$turns_cap" \
          --permission-mode bypassPermissions --output-format json
      else
        claude -p --resume "$session_id" "$(cat "$turn_file")" \
          --plugin-dir "$REPO" --model "${SCENARIO_MODEL:-$MODEL}" --max-turns "$turns_cap" \
          --permission-mode bypassPermissions --output-format json
      fi
    ) > "$turn_out" 2> "${turn_out%.json}.stderr" || true
    [[ -z "$session_id" ]] && session_id="$(json_field "$turn_out" session_id)"
    cost="$(json_field "$turn_out" total_cost_usd)"; [[ -z "$cost" ]] && cost=0
    total=$(python3 -c "print(round($total + $cost, 6))")
  done
  # Final JSON = last turn's, with the conversation-total cost.
  python3 - "$turn_out" "$out" "$total" <<'PYEOF'
import json, sys
src, dst, total = sys.argv[1], sys.argv[2], float(sys.argv[3])
try:
    d = json.load(open(src))
except Exception:
    d = {}
d["total_cost_usd"] = total
json.dump(d, open(dst, "w"))
PYEOF
}

# json_field <file> <key> — top-level string/number field, empty if absent.
json_field() {
  python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    v = d.get(sys.argv[2], "")
    print(v if v is not None else "")
except Exception:
    print("")
' "$1" "$2"
}

# result_text <file> — the model'\''s final text from a -p json result.
result_text() {
  python3 -c '
import json, sys
try:
    print(json.load(open(sys.argv[1])).get("result", ""))
except Exception:
    print("")
' "$1"
}

# packet_json <project_dir> — status report JSON (script may exit 1 on stale; ignore).
packet_json() {
  python3 "$REPO/scripts/protocol_status.py" "$1" --json 2>/dev/null || true
}

fail() { echo "    ASSERT FAIL: $*" >&2; return 1; }
