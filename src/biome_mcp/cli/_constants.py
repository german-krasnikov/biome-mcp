"""Shared CLI constants — no imports from other cli modules."""
from biome_mcp.errors import ErrorCode

CLI_CONFIG_FILENAME = "cli-config.json"

TOOL_HINT_THRESHOLD = 30

BUILTIN_DESCS: dict[str, str] = {
    "help": "Show this help or help for a command",
    "list": "List available tools",
    "describe": "Show tool schema and parameters",
    "call": "Call a tool (shortcut: <tool> [key=value ...])",
    "batch": "Execute batch DSL",
    "shell": "Interactive REPL with tab-completion",
    "serve": "Start MCP stdio server",
}

BUILTIN_USAGE: dict[str, str] = {
    "list": "list [--ns NS] [--effect read|write] [--grep TEXT] [--json] [--flat]",
    "describe": "describe <tool> [--json]",
    "call": "call <tool> [key=value ...] [--follow INTERVAL] [--max-polls N] [--dry-run]",
    "batch": 'batch "<dsl>" | --file FILE | --stdin',
    "shell": "shell",
    "serve": "serve",
    "help": "help [subcommand]",
}

EXIT_MAP: dict[str, int] = {
    ErrorCode.COMMAND_NOT_FOUND: 2,
    ErrorCode.INVALID_ARGUMENTS: 3,
    ErrorCode.PERMISSION_DENIED: 4,
    ErrorCode.TIMEOUT: 5,
    ErrorCode.CONNECTION_LOST: 6,
    ErrorCode.INTERNAL_ERROR: 1,
    ErrorCode.CANCELLED: 130,
}
