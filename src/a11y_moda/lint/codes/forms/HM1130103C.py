"""HM1130103C lint — `<fieldset>` first child must be a non-empty `<legend>`.

JSX child traversal is harder than HTML — children can be dynamic
expressions, fragments, conditionals. We handle the common case (literal
JSX children with `<legend>` first) and emit `caveat` when the first
child is a JSX expression or otherwise unanalysable.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, find_html_elements, has_spread_props


def _first_jsx_child_element(jsx_element):
    """Return the first JSX child element node, plus a flag indicating whether
    a non-element child (e.g. expression, conditional) precedes it."""
    saw_dynamic = False
    for child in jsx_element.children:
        # Skip the opening tag itself; we want body children.
        if child.type in ("jsx_opening_element", "jsx_self_closing_element",
                          "jsx_closing_element", "jsx_text"):
            # jsx_text may be whitespace; ignore for "first child" semantics.
            continue
        if child.type == "jsx_expression":
            # `{...}` — could render anything.
            saw_dynamic = True
            continue
        if child.type in ("jsx_element", "jsx_self_closing_element"):
            return child, saw_dynamic
        # Other node types (comments etc.) — ignore.
    return None, saw_dynamic


def _jsx_element_name(node):
    if node.type == "jsx_element":
        opening = next((c for c in node.children if c.type == "jsx_opening_element"), None)
    else:
        opening = node
    if opening is None:
        return None
    for c in opening.children:
        if c.type == "identifier":
            return c.text.decode("utf-8", errors="replace")
    return None


def _jsx_element_text(node) -> str:
    """Concatenate jsx_text children of an element. Doesn't follow expressions."""
    chunks: list[str] = []
    def walk(n):
        if n.type == "jsx_text":
            chunks.append(n.text.decode("utf-8", errors="replace"))
        for c in n.children:
            walk(c)
    walk(node)
    return "".join(chunks)


@register
class FieldsetLegendLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130103C",
        guideline="1.3.1",
        level=Level.A,
        desc="<fieldset> 第一個子元素需為非空 <legend>",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for fs in find_html_elements(parsed.tree, "fieldset"):
                # Walk for first nested element node.
                first = _first_html_child_element(fs)
                if first is None:
                    yield self._issue(status="fail",
                        message="<fieldset> 為空 — 不應作純視覺用途",
                        node=fs)
                    continue
                from ...helpers import _html_tag_name
                name = _html_tag_name(first)
                if name != "legend":
                    yield self._issue(status="fail",
                        message=f"<fieldset> 第一個子元素應為 <legend>，目前為 <{name}>",
                        node=fs)
                    continue
                # Verify legend has text content.
                text = _html_element_text(first).strip()
                if not text:
                    yield self._issue(status="fail",
                        message="<legend> 內文為空 — 必須提供群組標題",
                        node=first)
            return

        # JSX path
        for fs in find_jsx_elements(parsed.tree, "fieldset"):
            # Self-closing form: <fieldset /> or <fieldset {...props} />.
            # Has no body content at all. If it has spread, this is most
            # likely a wrapper component re-exporting fieldset; we can't
            # tell from this file. Skip silently — the responsibility lies
            # with the consumer who instantiates the wrapper.
            if fs.type == "jsx_self_closing_element":
                if has_spread_props(fs):
                    continue
                yield self._issue(status="fail",
                    message="<fieldset /> 為空 — 不應作純視覺用途",
                    node=fs)
                continue

            # Paired form: <fieldset>...</fieldset>. Look at body children.
            parent = fs.parent
            first, saw_dynamic = _first_jsx_child_element(parent)
            if first is None:
                # No static element child. If we saw dynamic (`{children}`,
                # `{x && <y/>}`) the children come from outside this file —
                # this is a wrapper component pattern (Radix/Shadcn/HeadlessUI
                # all use it). Responsibility shifts to consumer. Skip.
                if saw_dynamic:
                    continue
                # Truly empty — <fieldset></fieldset>.
                yield self._issue(status="fail",
                    message="<fieldset> 為空 — 不應作純視覺用途",
                    node=fs)
                continue
            if saw_dynamic:
                # Dynamic expression precedes the first element child.
                # Order can't be statically guaranteed.
                yield self._issue(status="caveat",
                    message="<fieldset> 開頭含動態表達式 — 無法確認 <legend> 是否為第一個子元素",
                    node=fs)
                continue
            name = _jsx_element_name(first)
            if name != "legend":
                yield self._issue(status="fail",
                    message=f"<fieldset> 第一個子元素應為 <legend>，目前為 <{name}>",
                    node=fs)
                continue
            text = _jsx_element_text(first).strip()
            if not text:
                yield self._issue(status="caveat",
                    message="<legend> 無靜態文字內容 — 請確認 runtime 給的文字非空",
                    node=first)


def _first_html_child_element(elem):
    """First nested `element` node inside an HTML element (skipping text/whitespace)."""
    for child in elem.children:
        if child.type in ("element", "self_closing_tag"):
            return child
    # Some elements have content wrapped — recurse one level if needed.
    return None


def _html_element_text(elem) -> str:
    chunks: list[str] = []
    def walk(node):
        if node.type == "text":
            chunks.append(node.text.decode("utf-8", errors="replace"))
        for c in node.children:
            walk(c)
    walk(elem)
    return "".join(chunks)
