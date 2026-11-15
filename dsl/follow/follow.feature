# Follow — persistent polling for CLI call subcommand.
# Source: src/biome_mcp/cli/follow.py, follow_policy.py

FEATURE followLoop USES service
  STATE poll : number = 0
  STATE consecutive_errors : number = 0
  FACT interval : number
  FACT max_polls : number?
  FACT max_retries : number = 0

  ACTION poll_tool
  ACTION stop
  ACTION retry

  DECISION is_done
  DECISION is_fatal

  SHOW poll, consecutive_errors
  EXAMPLES follow.examples
END
