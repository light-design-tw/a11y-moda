"""GN1210200E lint — role=dialog elements should have a close button (heuristic)."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr, _html_tag_name,
)


_CLOSE_RE = re.compile(r"close|關閉|cancel|取消|×|✕", re.IGNORECASE)


@register
class DialogHasCloseLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1210200E",
        guideline="2.1.2",
        level=Level.A,
        desc="role=dialog 元件應提供明確關閉按鈕",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                role = get_html_attr(el, "role")
                if role.kind != "literal" or role.value != "dialog":
                    continue
                if not self._html_has_close(el):
                    yield self._issue(status="info",
                        message="role=dialog 元件缺明確關閉按鈕，可能造成焦點受困",
                        node=el)
                    return
            return

        for el in find_jsx_elements(parsed.tree):
            role = get_attr(el, "role")
            if role.kind != "literal" or role.value != "dialog":
                continue
            parent = el.parent if el.type == "jsx_opening_element" else el
            if not self._jsx_has_close(parent):
                yield self._issue(status="info",
                    message="role=dialog 元件缺明確關閉按鈕，可能造成焦點受困",
                    node=el)
                return

    @staticmethod
    def _html_has_close(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) in ("button", "a"):
                # Check text content
                chunks: list[str] = []
                def collect(x):
                    if x.type == "text":
                        chunks.append(x.text.decode("utf-8", errors="replace"))
                    for c in x.children:
                        collect(c)
                collect(n)
                if _CLOSE_RE.search("".join(chunks)):
                    return True
                label = get_html_attr(n, "aria-label")
                if label.kind == "literal" and label.value and _CLOSE_RE.search(label.value):
                    return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _jsx_has_close(jsx_element) -> bool:
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in n.children if c.type == "identifier"), "")
                if tag in ("button", "a"):
                    label = get_attr(n, "aria-label")
                    if label.kind == "literal" and label.value and _CLOSE_RE.search(label.value):
                        return True
                    # Walk parent jsx_element for jsx_text
                    parent = n.parent
                    if parent and parent.type == "jsx_element":
                        chunks: list[str] = []
                        def collect(x):
                            if x.type == "jsx_text":
                                chunks.append(x.text.decode("utf-8", errors="replace"))
                            for c in x.children:
                                collect(c)
                        collect(parent)
                        if _CLOSE_RE.search("".join(chunks)):
                            return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
