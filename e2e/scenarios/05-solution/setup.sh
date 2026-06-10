#!/usr/bin/env bash
# Blank the fixture's solution so solution-brainstorming has real work to do.
# Text must match a TEMPLATE_MARKER in protocol_status.py so status reads "empty".
set -euo pipefail
PROJ="$1"
cat > "$PROJ/.clarity-protocol/solution/solution.md" <<'EOF'
# Solution

[To be determined. Run solution brainstorming to develop this.]
EOF
cat > "$PROJ/.clarity-protocol/solution/solution-summary.md" <<'EOF'
# Solution Summary

[To be determined. This summary is generated during solution brainstorming and updated during architecture design.]
EOF
