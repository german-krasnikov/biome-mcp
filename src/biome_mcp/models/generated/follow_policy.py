# Generated from follow-policy.data-contract
# source-sha256=20d01742d85aadf88190c1dad99fdfa9e9e42e421043d3eeb5604326019e529d
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class FollowPolicy:
    interval_bounds_min: float
    interval_bounds_max: float
    max_retries: float
    poll_timeout: float | None
