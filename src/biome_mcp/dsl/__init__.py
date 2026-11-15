"""DSL codegen — parse TOOL blocks, generate Python descriptors + schema + help."""
from biome_mcp.dsl.codegen import gen_descriptors, gen_help_text, gen_schema_init
from biome_mcp.dsl.lock import create_lock, verify_lock
from biome_mcp.dsl.parser import ToolDecl, parse_tools

__all__ = [
    "ToolDecl",
    "create_lock",
    "gen_descriptors",
    "gen_help_text",
    "gen_schema_init",
    "parse_tools",
    "verify_lock",
]
