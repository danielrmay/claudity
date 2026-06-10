FIXTURE="with-fixture"
MAX_TURNS=25
# Haiku reliably wrote the decision document but skipped the final
# --record-decision state step once the MCP server entered the context
# (measured 2026-06-10: pre-MCP 3/3, post-MCP 0/3, +preamble warning 1/3).
# Sonnet-class models follow the guide's record step; same remedy as the
# ambient conversational scenarios.
MODEL_FLOOR="sonnet"
