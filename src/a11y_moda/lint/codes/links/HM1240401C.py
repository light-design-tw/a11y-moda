"""HM1240401C lint — `<a href>` needs accessible text.

Sources of accessible text (any one):
- visible text content
- aria-label attribute
- img with non-empty alt inside
- svg with role="img" and aria-label inside

JSX dynamic text/label → caveat.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr,
    find_html_elements, get_html_attr, _html_tag_name,
)


@register
class LinkAccessibleTextLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1240401C",
        guideline="2.4.4",
        level=Level.A,
        desc="<a href> 需有鏈結文字 (text / aria-label / img alt / svg label)",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed):
        for a in find_html_elements(parsed.tree, "a"):
            href = get_html_attr(a, "href")
            if href.kind != "literal" or not href.value:
                continue
            if self._html_text(a).strip():
                continue
            label = get_html_attr(a, "aria-label")
            if label.kind == "literal" and label.value:
                continue
            # img alt or svg label
            if self._html_has_named_visual(a):
                continue
            yield self._issue(status="fail",
                message="<a> 無可訪文字 (text / aria-label / img alt 皆缺)",
                node=a)

    def _check_jsx(self, parsed):
        for a in find_jsx_elements(parsed.tree, "a"):
            href = get_attr(a, "href")
            if href.kind == "missing":
                continue
            parent = a.parent if a.type == "jsx_opening_element" else a
            static_text = self._jsx_static_text(parent).strip()
            has_dynamic = self._jsx_has_expression(parent)
            label = get_attr(a, "aria-label")
            label_present = label.kind in ("literal", "boolean", "dynamic") and (
                label.kind != "literal" or label.value
            )
            if static_text or label_present:
                continue
            if self._jsx_has_named_visual(parent):
                continue
            if has_dynamic:
                yield self._issue(status="caveat",
                    message="<a> 鏈結內容為動態值 — 請確認 runtime 提供可訪文字",
                    node=a)
                continue
            yield self._issue(status="fail",
                message="<a> 無可訪文字 — 應提供 text / aria-label / 帶 alt 的 img",
                node=a)

    @staticmethod
    def _html_text(node) -> str:
        chunks: list[str] = []
        def walk(n):
            if n.type == "text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(node)
        return "".join(chunks)

    @staticmethod
    def _html_has_named_visual(a) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                name = _html_tag_name(n)
                if name == "img":
                    alt = get_html_attr(n, "alt")
                    if alt.kind == "literal" and alt.value:
                        return True
                if name == "svg":
                    role = get_html_attr(n, "role")
                    if role.kind == "literal" and role.value == "img":
                        label = get_html_attr(n, "aria-label")
                        if label.kind == "literal" and label.value:
                            return True
            return any(walk(c) for c in n.children)
        return walk(a)

    @staticmethod
    def _jsx_static_text(jsx_element) -> str:
        chunks: list[str] = []
        def walk(n):
            if n.type == "jsx_text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(jsx_element)
        return "".join(chunks)

    @staticmethod
    def _jsx_has_expression(jsx_element) -> bool:
        def walk(n):
            if n.type == "jsx_expression":
                return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)

    @staticmethod
    def _jsx_has_named_visual(jsx_element) -> bool:
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                name = next((c.text.decode("utf-8", errors="replace")
                             for c in n.children if c.type == "identifier"), "")
                if name == "img":
                    alt = get_attr(n, "alt")
                    if alt.kind in ("literal", "dynamic", "boolean") and (
                        alt.kind != "literal" or alt.value
                    ):
                        return True
                if name == "svg":
                    role = get_attr(n, "role")
                    if role.kind == "literal" and role.value == "img":
                        label = get_attr(n, "aria-label")
                        if label.kind in ("literal", "dynamic"):
                            if label.kind != "literal" or label.value:
                                return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
