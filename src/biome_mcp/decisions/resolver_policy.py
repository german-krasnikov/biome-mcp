# Generated from resolver.logic
# source-sha256=1043a709fe26f67fb5b4f824f93e48b259e557292e27de394d9bc5cd2d42ffe7
# Edit the source, then run biome generate.

from __future__ import annotations

import math
import typing as _typing
from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class ConnectionSourceValues:
    CONFIG = "config"
    DEFAULT = "default"
    ENV = "env"
    FLAG = "flag"
    LOCK = "lock"
    PORT_FILE = "port_file"


@dataclass(frozen=True, slots=True)
class ConnectionSourceInput:
    resolver_cli_port_present: bool
    resolver_config_port_present: bool
    resolver_env_port_present: bool
    resolver_lock_available: bool
    resolver_port_file_available: bool


def connection_source(inp: ConnectionSourceInput) -> str:
    """Checks every input against the contract, then decides."""
    _check("resolver.cli_port_present", inp.resolver_cli_port_present, "bool")
    _check("resolver.config_port_present", inp.resolver_config_port_present, "bool")
    _check("resolver.env_port_present", inp.resolver_env_port_present, "bool")
    _check("resolver.lock_available", inp.resolver_lock_available, "bool")
    _check("resolver.port_file_available", inp.resolver_port_file_available, "bool")
    return _decide_connection_source(inp)


__all__ = [
    "LogicInputError",
    "ConnectionSourceValues",
    "ConnectionSourceInput",
    "connection_source",
]


# Unchecked evaluators: reachable only through the checked functions above.
def _check(
    fact_id: str,
    value: object,
    kind: str,
    lo: float | None = None,
    hi: float | None = None,
    integer: bool = False,
    values: tuple[str, ...] = (),
) -> None:
    if kind == "bool":
        ok = isinstance(value, bool)
    elif kind == "number":
        ok = (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
        number = _typing.cast("float", value)
        ok = ok and (lo is None or number >= lo) and (hi is None or number <= hi)
        if integer:
            ok = ok and float(number).is_integer() and abs(number) <= 9007199254740991
    elif kind == "enum":
        ok = isinstance(value, str) and value in values
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_connection_source(s: ConnectionSourceInput) -> str:
    # rule: flag (priority 10)
    if s.resolver_cli_port_present is True:
        return "flag"
    # rule: env (priority 20)
    if s.resolver_env_port_present is True:
        return "env"
    # rule: config (priority 30)
    if s.resolver_config_port_present is True:
        return "config"
    # rule: port_file (priority 40)
    if s.resolver_port_file_available is True:
        return "port_file"
    # rule: lock (priority 50)
    if s.resolver_lock_available is True:
        return "lock"
    return "default"
