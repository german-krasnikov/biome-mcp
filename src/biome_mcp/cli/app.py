"""BiomeCLI — dispatch, ToolProvider Protocol, ToolInfo TypedDict."""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    NoReturn,
    NotRequired,
    Protocol,
    TypedDict,
    runtime_checkable,
)

if TYPE_CHECKING:
    from biome_mcp.cli.connection import ConnectionSpec
    from biome_mcp.cli.follow_policy import FollowPolicy


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
        spec: ConnectionSpec | None = None,
        follow: FollowPolicy | None = None,
    ) -> None:
        self._provider = provider
        self._name = name
        self._version = version
        self._serve = serve
        self._schema_registry = schema_registry
        self._spec = spec
        self._follow = follow
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
        self._registry["call"] = make_call_handler(
            self._provider, spec=self._spec, follow=self._follow
        )
        self._registry["batch"] = make_batch_handler(self._provider)
        self._registry["shell"] = self._make_shell_handler()
        # help is registered last so it sees the full registry
        self._registry["help"] = make_help_handler(self._name, self._registry)

    def _make_shell_handler(self) -> Callable[[list[str]], int]:
        cli = self
        def handler(argv: list[str]) -> int:
            from biome_mcp.cli.shell import run_shell
            return run_shell(cli)
        return handler

    @property
    def provider(self) -> ToolProvider:
        return self._provider

    @property
    def registry(self) -> dict[str, Callable[[list[str]], int]]:
        return self._registry

    def add(self, name: str, handler: Callable[[list[str]], int]) -> None:
        """Register (or override) a subcommand."""
        self._registry[name] = handler

    def dispatch_one(self, argv: list[str]) -> int:
        """Route a single command, return exit code (no sys.exit)."""
        if not argv:
            if self._serve:
                self._serve()
                return 0
            self._registry["help"]([])
            return 0

        cmd, *rest = argv

        if cmd == "serve":
            if self._serve:
                self._serve()
                return 0
            print(
                f"error: no serve callback; run `{self._name} help`",
                file=sys.stderr,
            )
            return 1

        if cmd in self._registry:
            return self._registry[cmd](rest)

        # --help on any token → describe that tool
        if "--help" in rest or "-h" in rest:
            stripped = [a for a in rest if a not in ("--help", "-h")]
            return self._registry["describe"]([cmd, *stripped])

        # Namespace prefix: `cli scene` → list scene.* tools
        from biome_mcp.cli.formatters import tools_by_ns_prefix
        if not rest and self._provider.get_tool(cmd) is None:
            ns_tools = tools_by_ns_prefix(cmd, self._provider)
            if len(ns_tools) >= 2:
                return self._registry["list"](["--ns", cmd])

        # Implicit call: treat unknown subcommands as tool names
        return self._registry["call"]([cmd, *rest])

    def dispatch(self, argv: list[str] | None = None) -> NoReturn:
        if argv is None:
            argv = sys.argv[1:]
        sys.exit(self.dispatch_one(argv))
