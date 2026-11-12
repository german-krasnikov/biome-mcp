"""Tree compression tests — hierarchy rendering with budget."""

from biome_mcp.render.tree import TreeNode, compress_tree, render_tree


def _sample_tree(depth=3, children=3) -> TreeNode:
    if depth == 0:
        return TreeNode(label="leaf")
    kids = tuple(
        TreeNode(
            label=f"child_{i}",
            children=(_sample_tree(depth - 1, children),) if depth > 1 else (),
            data={"id": i},
        )
        for i in range(children)
    )
    return TreeNode(label="root", children=kids)


def test_render_simple():
    root = TreeNode(label="Root", children=(
        TreeNode(label="A"),
        TreeNode(label="B", data={"x": 1}),
    ))
    text = render_tree(root)
    assert "Root" in text
    assert "  A" in text
    assert "  B (x=1)" in text


def test_render_max_depth():
    deep = TreeNode(label="L0", children=(
        TreeNode(label="L1", children=(
            TreeNode(label="L2", children=(
                TreeNode(label="L3"),
            )),
        )),
    ))
    text = render_tree(deep, max_depth=2)
    assert "L0" in text
    assert "L1" in text
    assert "L2" in text
    assert "elided" in text


def test_render_budget():
    root = _sample_tree(depth=4, children=5)
    text = render_tree(root, budget=200)
    full = render_tree(root, budget=100000)
    assert len(text) < len(full)


def test_compress_tree_prunes():
    root = _sample_tree(depth=5, children=4)
    pruned = compress_tree(root, budget=200)
    # Pruned tree should have fewer levels
    text = render_tree(pruned)
    assert len(text) <= 300


def test_empty_tree():
    root = TreeNode(label="solo")
    text = render_tree(root)
    assert text == "solo"
