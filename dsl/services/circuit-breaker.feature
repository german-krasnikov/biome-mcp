# CircuitBreaker — state machine for backend resilience.
# Source: src/biome_mcp/circuit_breaker.py

FEATURE circuitBreaker USES service
  STATE state : text = "closed"
  STATE failures : number = 0
  FACT threshold : number
  FACT cooldown : number
  STATE opened_at : number = 0.0

  ACTION record_success
  ACTION record_failure
  ACTION allow_request
  ACTION reset
  ACTION release_probe
  ACTION get_status
  ACTION remaining

  DECISION is_open

  SHOW state, failures, threshold, cooldown, opened_at
  EXAMPLES circuitBreaker.examples
END
