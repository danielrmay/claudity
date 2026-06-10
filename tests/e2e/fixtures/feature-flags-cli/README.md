# e2e fixture: feature-flags CLI

A deliberately skeletal `.clarity-protocol/` packet used by the e2e
scenarios. Its exact states are load-bearing: a recorded decision with a
fired reconsideration trigger (solution.md edited after decision-01), one
analyzed failure with a management plan, an archived pool item, mostly
template downstream documents (so the status engine has stale/empty/empty
states to route on), and the embedded CLAUDE.md snippet every real embedded
project carries. `tests/test_plugin_structure.py` pins this packet to a
frozen manifest — change it only deliberately, updating the manifest and
re-checking each scenario's assumptions.

For a real, showcase-quality packet, see `examples/`.
