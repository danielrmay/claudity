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

# run_claude <project_dir> <prompt_file> <max_turns> <result_json_out>
# Headless run with the plugin loaded from the repo. Never fails the shell;
# callers inspect the JSON and artifacts.
run_claude() {
  local proj="$1" prompt_file="$2" turns="$3" out="$4"
  (
    cd "$proj" || exit 1
    claude -p "$(cat "$prompt_file")" \
      --plugin-dir "$REPO" \
      --model "$MODEL" \
      --max-turns "$turns" \
      --permission-mode bypassPermissions \
      --output-format json
  ) > "$out" 2> "${out%.json}.stderr" || true
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
