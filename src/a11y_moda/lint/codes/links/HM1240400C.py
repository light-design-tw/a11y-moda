"""HM1240400C lint — `<img>` inside `<a>` must not have alt equal to link text.

When a link contains both an image and adjacent text, the image alt
should be empty (decorative, screen reader uses the text) OR have
different content. Same alt+text → screen reader announces twice.

JSX dynamic alt values OR dynamic link text → caveat (can't compare
two unknowns). HTML literal compare is straightforward.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr,
    find_html_elements, get_html_attr,
)


@register
class AdjacentImgTextLinkLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1240400C",
        guideline="2.4.4",
        level=Level.A,
        desc="毗鄰圖片與文字的連結，圖片 alt 不得與連結文字重複",
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
            link_text = self._html_text(a).strip()
            if not link_text:
                continue
            for img in self._html_descendants(a, "img"):
                alt = get_html_attr(img, "alt")
                if alt.kind == "literal" and alt.value == link_text:
                    yield self._issue(status="fail",
                        message="<a> 內 <img> alt 與鏈結文字相同 — 應為空 alt 或不同內容",
                        node=a)
                    break

    def _check_jsx(self, parsed):
        for a in find_jsx_elements(parsed.tree, "a"):
            href = get_attr(a, "href")
            if href.kind == "missing":
                continue
            # Get link text from the wrapping jsx_element body.
            parent = a.parent if a.type == "jsx_opening_element" else a
            link_text = self._jsx_text(parent).strip()
            link_text_dynamic = self._has_jsx_text_expressions(parent)
            for img in self._jsx_descendants(parent, "img"):
                alt = get_attr(img, "alt")
                if alt.kind == "literal" and link_text and alt.value == link_text:
                    yield self._issue(status="fail",
                        message="<a> 內 <img> alt 與鏈結文字相同 — 應為空 alt 或不同內容",
                        node=a)
                    break
                if alt.kind == "dynamic" or link_text_dynamic:
                    yield self._issue(status="caveat",
                        message="<a> 內 <img> alt 或鏈結文字為動態值 — 無法靜態比對是否重複",
                        node=a)
                    break

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
    def _html_descendants(node, tag):
        from ...helpers import _html_tag_name
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == tag:
                out.append(n)
            for c in n.children:
                walk(c)
        walk(node)
        return out

    @staticmethod
    def _jsx_text(jsx_element) -> str:
        chunks: list[str] = []
        def walk(n):
            if n.type == "jsx_text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(jsx_element)
        return "".join(chunks)

    @staticmethod
    def _has_jsx_text_expressions(jsx_element) -> bool:
        """True if body contains `{...}` expressions that may render text."""
        for child in jsx_element.children:
            if child.type == "jsx_expression":
                return True
        return False

    @staticmethod
    def _jsx_descendants(jsx_element, tag):
        out = []
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for c in n.children:
                    if c.type == "identifier" and c.text.decode("utf-8", errors="replace") == tag:
                        out.append(n)
                        break
            for c in n.children:
                walk(c)
        walk(jsx_element)
        return out
