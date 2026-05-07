"""AST query helpers for lint rules.

Tree-sitter's tsx grammar models JSX as a mix of `jsx_element` (with open/
close tags) and `jsx_self_closing_element`. Attribute names are
`property_identifier` children of `jsx_attribute`; values can be `string`
literals or `jsx_expression` (the `{...}` form).

These helpers normalise the raw node tree into easier shapes for rule
authors:

    find_jsx_elements(tree, "img")           → list of <img> nodes
    get_attr(elem, "alt")                    → AttrInfo with kind/value
    walk_html_elements(tree, "img")          → list of HTML <img> nodes (tree-sitter-html)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Literal


# Where the attribute came from / how it was specified.
AttrKind = Literal["missing", "boolean", "empty", "literal", "dynamic"]


@dataclass
class AttrInfo:
    kind: AttrKind
    value: str | None      # literal text when kind == "empty" or "literal"
    raw: str | None        # raw source text of the value expression (for snippets)


_JSX_ELEMENT_HEADS = {"jsx_opening_element", "jsx_self_closing_element"}


def _element_name(node) -> str | None:
    """JSX element name lives as the first `identifier` child of an opening tag."""
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8", errors="replace")
    return None


def find_jsx_elements(tree, name: str | None = None) -> list:
    """Yield JSX opening or self-closing element nodes (matching `name` if given).

    For a paired element like `<a>...</a>`, the opening tag is the head we
    return — the closing tag is structural noise. For `<img />`, the element
    IS the self-closing node.
    """
    out: list = []
    def walk(node):
        if node.type in _JSX_ELEMENT_HEADS:
            if name is None or _element_name(node) == name:
                out.append(node)
        for child in node.children:
            walk(child)
    walk(tree.root_node)
    return out


def find_jsx_elements_any(tree, names: tuple[str, ...]) -> list:
    """Same as find_jsx_elements but matches any of several element names."""
    out: list = []
    def walk(node):
        if node.type in _JSX_ELEMENT_HEADS:
            n = _element_name(node)
            if n in names:
                out.append(node)
        for child in node.children:
            walk(child)
    walk(tree.root_node)
    return out


def has_spread_props(jsx_element) -> bool:
    """True if the element has `{...rest}` spread — attributes may come from
    elsewhere and the static check can't see them. Rules treat this as a
    caveat: don't claim the attribute is missing if spread might supply it.

    Tree-sitter shape: jsx_expression containing a spread_element child.
    """
    for child in jsx_element.children:
        if child.type != "jsx_expression":
            continue
        for sub in child.children:
            if sub.type == "spread_element":
                return True
    return False


def get_attr(jsx_element, attr_name: str) -> AttrInfo:
    """Look up an attribute on a JSX element. Returns AttrInfo describing how it
    was specified (missing / boolean / empty literal / non-empty literal / dynamic).
    """
    for child in jsx_element.children:
        if child.type != "jsx_attribute":
            continue
        # Attribute name = first property_identifier inside.
        name_node = next((c for c in child.children if c.type == "property_identifier"), None)
        if name_node is None:
            continue
        if name_node.text.decode("utf-8", errors="replace") != attr_name:
            continue
        # Value (if any) follows the `=` token. Look for first string or jsx_expression.
        val_node = next(
            (c for c in child.children if c.type in ("string", "jsx_expression")),
            None,
        )
        if val_node is None:
            return AttrInfo(kind="boolean", value=None, raw=None)
        if val_node.type == "string":
            frag = next((c for c in val_node.children if c.type == "string_fragment"), None)
            text = frag.text.decode("utf-8", errors="replace") if frag is not None else ""
            return AttrInfo(
                kind="empty" if text == "" else "literal",
                value=text,
                raw=val_node.text.decode("utf-8", errors="replace"),
            )
        # jsx_expression: dynamic — `{...}`.
        return AttrInfo(
            kind="dynamic",
            value=None,
            raw=val_node.text.decode("utf-8", errors="replace"),
        )
    return AttrInfo(kind="missing", value=None, raw=None)


def position(node) -> tuple[int, int]:
    """tree-sitter rows/columns are 0-based; report 1-based for editor compat."""
    row, col = node.start_point
    return row + 1, col + 1


def snippet(node, max_len: int = 200) -> str:
    """Source text of a node, truncated. Tree-sitter returns bytes; decode safely."""
    text = node.text.decode("utf-8", errors="replace")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


# ---------------------------------------------------------------------------
# HTML helpers (tree-sitter-html grammar — different node names)
# ---------------------------------------------------------------------------

def find_html_elements(tree, tag: str | None = None) -> list:
    """tree-sitter-html uses `element` for paired tags and `self_closing_tag`
    for void elements. Both have a `tag_name` child somewhere in their open tag.
    """
    out: list = []
    def walk(node):
        if node.type in ("element", "self_closing_tag"):
            if tag is None or _html_tag_name(node) == tag:
                out.append(node)
        for child in node.children:
            walk(child)
    walk(tree.root_node)
    return out


def _html_tag_name(node) -> str | None:
    # For `element`, structure is: start_tag → tag_name. For `self_closing_tag`,
    # tag_name is a direct child.
    for child in node.children:
        if child.type == "start_tag":
            for sub in child.children:
                if sub.type == "tag_name":
                    return sub.text.decode("utf-8", errors="replace").lower()
        if child.type == "tag_name":
            return child.text.decode("utf-8", errors="replace").lower()
    return None


def get_html_attr(html_element, attr_name: str) -> AttrInfo:
    """HTML attributes are simpler — no dynamic expressions. Either present
    (literal value) or absent. Boolean attributes have no `=` so kind=boolean.
    """
    # Find the start_tag for paired elements; for self_closing_tag look directly.
    start_tag = None
    if html_element.type == "self_closing_tag":
        start_tag = html_element
    else:
        for child in html_element.children:
            if child.type == "start_tag":
                start_tag = child
                break
    if start_tag is None:
        return AttrInfo(kind="missing", value=None, raw=None)

    for attr in start_tag.children:
        if attr.type != "attribute":
            continue
        name_node = next((c for c in attr.children if c.type == "attribute_name"), None)
        if name_node is None:
            continue
        if name_node.text.decode("utf-8", errors="replace").lower() != attr_name.lower():
            continue
        val_node = next((c for c in attr.children if c.type in ("attribute_value", "quoted_attribute_value")), None)
        if val_node is None:
            return AttrInfo(kind="boolean", value=None, raw=None)
        # quoted_attribute_value wraps the literal in quotes; unwrap.
        if val_node.type == "quoted_attribute_value":
            inner = next((c for c in val_node.children if c.type == "attribute_value"), None)
            text = inner.text.decode("utf-8", errors="replace") if inner is not None else ""
        else:
            text = val_node.text.decode("utf-8", errors="replace")
        return AttrInfo(
            kind="empty" if text == "" else "literal",
            value=text,
            raw=val_node.text.decode("utf-8", errors="replace"),
        )
    return AttrInfo(kind="missing", value=None, raw=None)
