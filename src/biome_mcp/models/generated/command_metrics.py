# Generated from command-metrics.data-contract
# source-sha256=f6ff12bb49213481cbc0533ee12bbd40579a30fdc9fc409219ff2c52985058b3
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandMetrics:
    invocations: float
    errors: float
    total_duration_s: float
    last_duration_s: float
