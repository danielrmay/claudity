#!/usr/bin/env bash
# Check microsoft/clarity-agent for changes affecting Claudity's vendored set.
#
# Reads upstream.json (repo, pin, watch list, watch_new_files_in) and reports:
#   - commits ahead of the pin, and which changed files fall in the watch set
#   - new files in watched directories that aren't in the watch set yet
#   - the latest upstream release vs the recorded upstream_version
#
# Usage: scripts/upstream_check.sh [--pin SHA]
#   --pin overrides the recorded pin (useful for testing detection).
#
# Exit codes: 0 = in sync, 10 = upstream changes need review, 1 = error.
# Requires: gh (authenticated), python3.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$REPO_DIR/upstream.json"

PIN_OVERRIDE=""
if [[ "${1:-}" == "--pin" ]]; then
  PIN_OVERRIDE="${2:?--pin requires a SHA}"
fi

UPSTREAM_REPO="$(python3 -c "import json;print(json.load(open('$CONFIG'))['repo'])")"
PIN="${PIN_OVERRIDE:-$(python3 -c "import json;print(json.load(open('$CONFIG'))['pin'])")}"

WORK="$(mktemp -d /tmp/claudity-upstream-check.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

gh api "repos/$UPSTREAM_REPO/compare/$PIN...main" > "$WORK/compare.json" \
  || { echo "ERROR: could not compare $PIN...main on $UPSTREAM_REPO" >&2; exit 1; }
gh api "repos/$UPSTREAM_REPO/git/trees/main?recursive=1" > "$WORK/tree.json" \
  || { echo "ERROR: could not list main tree of $UPSTREAM_REPO" >&2; exit 1; }
gh api "repos/$UPSTREAM_REPO/releases/latest" --jq '.tag_name' > "$WORK/release.txt" 2>/dev/null \
  || echo "unknown" > "$WORK/release.txt"

python3 - "$CONFIG" "$PIN" "$WORK" <<'PYEOF'
import json, sys
from pathlib import Path

config_path, pin, work = sys.argv[1], sys.argv[2], Path(sys.argv[3])
cfg = json.load(open(config_path))
compare = json.loads((work / "compare.json").read_text())
tree = json.loads((work / "tree.json").read_text())
latest_release = (work / "release.txt").read_text().strip()
repo = cfg["repo"]
recorded_version = cfg["upstream_version"]

watched = {w["upstream"]: w["local"] for w in cfg["watch"]}
new_dirs = tuple(cfg["watch_new_files_in"])

ahead = compare.get("ahead_by", 0)
changed = compare.get("files", [])
vendored_changes = [f for f in changed if f["filename"] in watched]

added = {f["filename"] for f in changed if f.get("status") == "added"}
tree_paths = {e["path"] for e in tree.get("tree", []) if e.get("type") == "blob"}
new_candidates = sorted(
    p for p in tree_paths
    if p.startswith(new_dirs)
    and p not in watched
    and not p.endswith("README.md")
    and p in added
)

release_drift = latest_release not in ("unknown", recorded_version)

lines = [f"# Upstream check: {repo}", ""]
lines.append(f"Pinned: `{pin}` (recorded upstream version {recorded_version})")
lines.append(f"Latest upstream release: **{latest_release}**")
lines.append(f"Commits on main since pin: **{ahead}**")
lines.append("")

action = bool(vendored_changes or new_candidates)
if vendored_changes:
    lines.append("## Vendored files changed upstream (need re-sync review)")
    lines.append("")
    for f in vendored_changes:
        lines.append(
            f"- `{f['filename']}` → `{watched[f['filename']]}` "
            f"(+{f['additions']}/-{f['deletions']}, {f['status']})"
        )
    lines.append("")
if new_candidates:
    lines.append("## New upstream files in watched directories (consider adopting)")
    lines.append("")
    for p in new_candidates:
        lines.append(f"- `{p}`")
    lines.append("")
if action:
    if release_drift:
        lines.append(
            f"Upstream has released {latest_release} since {recorded_version} — "
            f"a good re-pin point."
        )
        lines.append("")
    lines.append(f"Compare: https://github.com/{repo}/compare/{pin[:12]}...main")
    lines.append("")
    lines.append(
        "Follow the re-sync procedure in UPSTREAM.md; "
        "substitutions are governed by PORTING.md."
    )
else:
    lines.append("In sync: no vendored-path changes since the pin.")

print("\n".join(lines))
sys.exit(10 if action else 0)
PYEOF
