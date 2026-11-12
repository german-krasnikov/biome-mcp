# Architecture: biome-mcp

## Overview

biome-mcp — общий MCP/CLI фреймворк, извлечённый из unity-biome-mcp (~46K строк) и biome-browser-mcp (~16K строк). Устраняет ~13,500 строк дублирования между 3 проектами.

## Core Concept

Одна команда проходит одинаковые validation, policies и formatting через MCP, CLI и batch.

```
MCP adapter ──┐
CLI adapter ──┤── Executor ──→ Guard chain ──→ Handler ──→ Renderer
Batch entry ──┘       │
                 Registry (CommandDescriptor)
                 Policies (DSL-generated decisions)
```

## Package Structure

```
src/biome_mcp/
├── __init__.py              # version
├── errors.py                # ErrorCode enum + BiomeError (from Unity, fuller taxonomy)
├── models/
│   ├── descriptor.py        # CommandDescriptor — engine-agnostic tool contract
│   └── result.py            # CommandResult — Ok/Failed/Cancelled/TimedOut/Unknown
├── registry.py              # CommandDescriptor store + handler factory
├── executor.py              # validate → guard → execute → format (единый путь)
├── batch/
│   ├── lexer.py             # Batch DSL tokenizer (from Browser, typed)
│   ├── parser.py            # Batch DSL parser (from Browser)
│   ├── planner.py           # Batch plan validator (from Browser)
│   └── executor.py          # Sequential + native batch execution
├── plugins/
│   ├── loader.py            # Plugin discovery + lifecycle (from Browser)
│   └── manifest.py          # Plugin manifest validation
├── render/
│   ├── renderer.py          # PlainTextRenderer + budget (from Unity)
│   ├── tree.py              # Generic hierarchy compression engine
│   └── profiles.py          # Configurable compress rules (defaults, aliases)
├── transport/
│   ├── base.py              # Transport interface (connect, send, close)
│   ├── tcp.py               # TCP framing + heartbeat (from Unity)
│   └── stdio.py             # Stdio framing (from Browser)
├── doctor.py                # Diagnostic runner skeleton (from Unity)
├── metrics.py               # Counters + timers (from Unity)
├── decisions/
│   └── generated/           # DSL-generated Python decision functions
│       ├── mutability.py    # "is this a read or write?"
│       ├── retry.py         # "transient → retry, permanent → stop"
│       ├── batch_policy.py  # "stop/continue/rollback on error"
│       ├── error_class.py   # "transient/permanent/unknown"
│       ├── permission.py    # permission ladder
│       └── versionorder.py  # semver comparison
└── py.typed
```

## DSL Architecture

DSL генерирует Python + C# из одного источника. Используется DECISION engine из biome-dsl toolchain.

```
dsl/
├── biome.project             # Toolchain pin + GENERATE targets
├── content-lock.json         # SHA256 lock (source → generated)
├── decisions/
│   ├── mutability.logic      # "read or write?" — from unity-mcp
│   ├── mutability.contract   # Expected inputs/outputs
│   ├── mutability.examples   # Test rows
│   ├── retry.logic           # Generic retry (no Unity domain reload)
│   ├── batch_policy.logic    # NEW: stop/continue/rollback
│   ├── error_class.logic     # NEW: transient/permanent/unknown
│   ├── permission.logic      # Permission ladder — from unity-mcp
│   └── versionorder.logic    # Semver — from unity-mcp
└── constructs/
    └── (future: tool.construct, feature.construct)
```

## Donors

| Module | From | Why |
|--------|------|-----|
| errors | Unity | Fuller taxonomy |
| batch/ | Browser | Typed, split into modules |
| models/result | Browser | Typed CommandResult |
| plugins/ | Browser | Full lifecycle |
| render + compress | Unity | Budget + profiles |
| transport/tcp | Unity | TCP framing |
| transport/stdio | Browser | Stdio framing |
| doctor, metrics | Unity | More complete |
| decisions | Unity | More .logic files |
| registry, executor | New | Both existing ones insufficient |

## Key Interfaces

### CommandDescriptor

```python
@dataclass(frozen=True)
class CommandDescriptor:
    name: str                    # stable identifier (e.g. "scene.inspect")
    namespace: str               # grouping (e.g. "scene")
    summary: str                 # one-line help
    params: tuple[ParamSpec, ...]
    effect: CommandEffect        # read / write / idempotent_write
    batchable: bool
    requires: frozenset[str]     # capability requirements
```

### CommandResult

```python
@dataclass(frozen=True)
class CommandResult:
    status: CommandStatus        # ok / invalid_args / failed / cancelled / timed_out / unknown
    text: str                    # compact plain text for agent
    data: Any = None             # structured data (optional)
    complete: bool = True        # false = truncated
    error_code: str | None = None
```

### Transport (interface)

```python
class Transport(Protocol):
    async def connect(self) -> None: ...
    async def send(self, cmd: str, args: dict) -> dict: ...
    async def close(self) -> None: ...
    @property
    def connected(self) -> bool: ...
```

### GuardProvider (facts injection)

```python
class GuardProvider(Protocol):
    async def check(self, cmd: CommandDescriptor, args: dict) -> GuardResult: ...
```

Unity provides: `compile_errors`, `play_mode`, `domain_reload`.
Browser provides: `page_loading`, `navigation`, `cdp_disconnected`.

## Facts Injection Pattern

Core decisions define abstract rules. Engine adapters provide facts.

```python
# biome-mcp: generic retry rule
# retry.logic:
# RULE transient_connection
#   WHEN error.category == connection_lost
#   THEN retry(backoff: exponential, max: 3)

# unity adapter: provides Unity-specific facts
class UnityRetryFacts:
    domain_reload: bool       # → wait + retry
    compile_pending: bool     # → block writes

# browser adapter: provides browser-specific facts
class BrowserRetryFacts:
    page_navigating: bool     # → wait + retry
    cdp_disconnected: bool    # → reconnect + retry
```

## Stages

| Stage | Scope | Deliverables |
|-------|-------|-------------|
| 1 | Foundation | errors, descriptor, result, DSL decisions, content lock, tests |
| 2 | Execution | registry, executor, batch (from Browser), unity-mcp switches |
| 3 | Rendering | renderer, tree compress, transport (TCP + stdio) |
| 4 | Integration | browser-mcp switches, delete duplicated code |
| 5 | CLI | CLI adapter (list/describe/call/batch), FastMCP 4.x |

## Architecture (для Architect)

Architect проектирует каждый Stage отдельно. План в `Plans/<stage>.md` с grounded refs (file:line из доноров).

## Implementation Notes (для Developer)

- TDD: test first, fake in-memory backend
- Engine-agnostic: no `import mcp`, no Unity/CDP references
- Files < 200 lines
- Content lock: DSL-generated files verified by test

## Review Checklist (для Reviewer)

- [ ] Engine-agnostic boundary: no engine imports in `src/biome_mcp/`
- [ ] TDD compliance: test exists before implementation
- [ ] Content lock: generated files match DSL source
- [ ] CommandResult used consistently (no raw dicts/tuples)
- [ ] Plain text default for all renderers
