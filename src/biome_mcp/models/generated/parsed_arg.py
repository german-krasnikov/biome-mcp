# Generated from parsed-arg.data-contract
# source-sha256=30abb3b69e340ae744efa879733f31ff1b44f6667540ee2240dba7796f76cb0a
# Edit the source, then run biome generate.

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class LexicalKind(StrEnum):
    BARE = "bare"
    QUOTED = "quoted"
    BOOLEAN = "boolean"
    NULL = "null"
    NUMBER = "number"
    JSON_LITERAL = "json_literal"


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedArg:
    key: str
    kind: LexicalKind
    raw: str
    value: Any
