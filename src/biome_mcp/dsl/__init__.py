"""DSL codegen — parse TOOL blocks, generate Python descriptors + schema + help."""
from biome_mcp.dsl.parser import ToolDecl, parse_tools

__all__ = ["ToolDecl", "parse_tools"]
