"""GN1240100E lint — page must have a top-of-page skip link to main content.

HTML only. JSX root pages don't render <body>; the skip link usually
lives in a root layout component (Next App Router `layout.tsx` or
similar). Defer JSX detection to scan stage.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr, _html_tag_name


@register
class SkipLinkLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1240100E",
        guideline="2.4.1",
        level=Level.A,
        desc="頁面頂端應有 skip link 直接連往主要內容",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        bodies = find_html_elements(parsed.tree, "body")
        if not bodies:
            return
        body = bodies[0]
        # Look at first 8 <a href> in body order.
        anchors = self._first_n_anchors(body, 8)
        # Collect all element id attributes in the page so we can verify the
        # skip link target exists.
        ids = self._collect_ids(parsed.tree.root_node)
        for a in anchors:
            href = get_html_attr(a, "href")
            if href.kind != "literal" or not href.value:
                continue
            v = href.value.strip()
            if v.startswith("#") and len(v) > 1 and v[1:] in ids:
                return  # skip link found
        yield self._issue(status="fail",
            message='未發現指向主要內容的 skip link (頁首前幾個 <a href="#main"> 之類)',
            node=body)

    @staticmethod
    def _first_n_anchors(body, n):
        out = []
        def walk(node):
            if len(out) >= n:
                return
            if node.type in ("element", "self_closing_tag") and _html_tag_name(node) == "a":
                if get_html_attr(node, "href").kind in ("literal", "boolean"):
                    out.append(node)
                    if len(out) >= n:
                        return
            for c in node.children:
                walk(c)
                if len(out) >= n:
                    return
        walk(body)
        return out

    @staticmethod
    def _collect_ids(root):
        ids: set[str] = set()
        def walk(node):
            if node.type in ("element", "self_closing_tag"):
                a = get_html_attr(node, "id")
                if a.kind == "literal" and a.value:
                    ids.add(a.value)
            for c in node.children:
                walk(c)
        walk(root)
        return ids
