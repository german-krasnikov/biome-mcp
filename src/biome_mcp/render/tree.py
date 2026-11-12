"""Generic hierarchy compression — elide deep children under budget.

Engine-agnostic: works on any tree represented as nested dicts/lists.
Unity uses it for scene hierarchies, Browser for DOM trees.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TreeNode:
    label: str
    children: tuple[TreeNode, ...] = ()
    data: dict[str, Any] | None = None


def render_tree(root: TreeNode, *, max_depth: int = 10, budget: int = 4096) -> str:
    lines: list[str] = []
    _render(root, lines, depth=0, max_depth=max_depth, budget=budget)
    return "\n".join(lines)


def _render(
    node: TreeNode,
    lines: list[str],
    depth: int,
    max_depth: int,
    budget: int,
) -> int:
    used = 0
    indent = "  " * depth
    line = f"{indent}{node.label}"
    if node.data:
        compact = " ".join(f"{k}={v}" for k, v in node.data.items())
        line = f"{line} ({compact})"
    lines.append(line)
    used += len(line) + 1

    if used >= budget:
        lines.append(f"{indent}  ... [budget exceeded]")
        return used

    if depth >= max_depth and node.children:
        lines.append(f"{indent}  ... [{len(node.children)} children elided]")
        return used + 30

    for child in node.children:
        remaining = budget - used
        if remaining <= 0:
            lines.append(f"{indent}  ... [{len(node.children)} children, budget exceeded]")
            break
        used += _render(child, lines, depth + 1, max_depth, remaining)
    return used


def compress_tree(root: TreeNode, *, budget: int = 4096) -> TreeNode:
    """Prune tree to fit within budget chars."""
    text = render_tree(root, budget=budget)
    if len(text) <= budget:
        return root
    # Progressive depth reduction
    for max_d in range(10, 0, -1):
        text = render_tree(root, max_depth=max_d, budget=budget)
        if len(text) <= budget:
            return _prune_to_depth(root, max_d)
    return TreeNode(label=root.label, data=root.data)


def _prune_to_depth(node: TreeNode, max_depth: int, depth: int = 0) -> TreeNode:
    if depth >= max_depth:
        return TreeNode(label=node.label, data=node.data)
    children = tuple(
        _prune_to_depth(c, max_depth, depth + 1) for c in node.children
    )
    return TreeNode(label=node.label, children=children, data=node.data)
