"""BiomeCLI — dispatch, ToolProvider Protocol, ToolInfo TypedDict."""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, NoReturn, NotRequired, Protocol, TypedDict, runtime_checkable


class ToolInfo(TypedDict):
    name: str
    description: str
    input_schema: dict
    effect: NotRequired[str]   # "read" | "write" | "idempotent_write" | "delete"
    namespace: NotRequired[str]


@runtime_checkable
class ToolProvider(Protocol):
    def list_tools(self) -> list[ToolInfo]: ...
    def get_tool(self, name: str) -> ToolInfo | None: ...
    def call_tool_sync(self, name: str, args: dict[str, Any]) -> Any: ...


class BiomeCLI:
    def __init__(
        self,
        provider: ToolProvider,
        *,
        name: str = "biome",
        version: str = "",
        serve: Callable[[], None] | None = None,
        schema_registry: Any = None,
    ) -> None:
        self._provider = provider
        self._name = name
        self._version = version
        self._serve = serve
        self._schema_registry = schema_registry
        self._registry: dict[str, Callable[[list[str]], int]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        from biome_mcp.cli.generic import (
            make_batch_handler,
            make_call_handler,
            make_describe_handler,
            make_help_handler,
            make_list_handler,
        )
        self._registry["list"] = make_list_handler(self._provider)
        self._registry["describe"] = make_describe_handler(
            self._provider, registry=self._schema_registry, app_name=self._name,
        )
        self._registry["call"] = make_call_handler(self._provider)
        self._registry["batch"] = make_batch_handler(self._provider)
        # help is registered last so it sees the full registry
        self._registry["help"] = make_help_handler(self._name, self._registry)

    def add(self, name: str, handler: Callable[[list[str]], int]) -> None:
        """Register (or override) a subcommand."""
        self._registry[name] = handler

    def dispatch(self, argv: list[str] | None = None) -> NoReturn:
        if argv is None:
            argv = sys.argv[1:]

        if not argv:
            if self._serve:
                self._serve()
                sys.exit(0)
            self._registry["help"]([])
            sys.exit(0)

        cmd, *rest = argv

        if cmd == "serve":
            if self._serve:
                self._serve()
                sys.exit(0)
            print(
                f"error: no serve callback; run `{self._name} help`",
                file=sys.stderr,
            )
            sys.exit(1)

        if cmd in self._registry:
            code = self._registry[cmd](rest)
            sys.exit(code)

        print(
            f"error: unknown command '{cmd}'; run `{self._name} help`",
            file=sys.stderr,
        )
        sys.exit(1)
