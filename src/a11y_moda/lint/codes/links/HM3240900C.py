"""HM3240900C lint — `<a>` title attribute must not duplicate link text or img alt.

AAA-level. JSX literal compare; dynamic title → caveat.
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
class LinkTitleNotDuplicateLint(LintRule):
    meta = RuleMeta(
        rule_id="HM3240900C",
        guideline="2.4.9",
        level=Level.AAA,
        desc="<a> 的 title 屬性不應重複 link 文字或 img alt",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for a in find_html_elements(parsed.tree, "a"):
                href = get_html_attr(a, "href")
                if href.kind != "literal" or not href.value:
                    continue
                title = get_html_attr(a, "title")
                if title.kind != "literal":
                    continue
                text = self._html_text(a).strip()
                if text and text == title.value:
                    yield self._issue(status="fail",
                        message="<a> title 與鏈結文字重複",
                        node=a)
                    continue
                # check imgs
                if self._has_html_img_with_alt(a, title.value):
                    yield self._issue(status="fail",
                        message="<a> title 與內 <img alt> 重複",
                        node=a)
            return

        for a in find_jsx_elements(parsed.tree, "a"):
            href = get_attr(a, "href")
            if href.kind == "missing":
                continue
            title = get_attr(a, "title")
            if title.kind == "missing":
                continue
            if title.kind == "dynamic":
                yield self._issue(status="caveat",
                    message="<a> title 為動態值 — 無法靜態比對是否與鏈結文字/alt 重複",
                    node=a)
                continue
            if title.kind != "literal":
                continue
            parent = a.parent if a.type == "jsx_opening_element" else a
            text = self._jsx_text(parent).strip()
            if text and text == title.value:
                yield self._issue(status="fail",
                    message="<a> title 與鏈結文字重複",
                    node=a)
                continue
            if self._has_jsx_img_with_alt(parent, title.value):
                yield self._issue(status="fail",
                    message="<a> title 與內 <img alt> 重複",
                    node=a)

    @staticmethod
    def _html_text(node) -> str:
        chunks = []
        def walk(n):
            if n.type == "text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(node)
        return "".join(chunks)

    @staticmethod
    def _has_html_img_with_alt(node, target) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == "img":
                alt = get_html_attr(n, "alt")
                if alt.kind == "literal" and alt.value == target:
                    return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _jsx_text(jsx_element) -> str:
        chunks = []
        def walk(n):
            if n.type == "jsx_text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(jsx_element)
        return "".join(chunks)

    @staticmethod
    def _has_jsx_img_with_alt(jsx_element, target) -> bool:
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                name = next((c.text.decode("utf-8", errors="replace")
                             for c in n.children if c.type == "identifier"), "")
                if name == "img":
                    alt = get_attr(n, "alt")
                    if alt.kind == "literal" and alt.value == target:
                        return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
