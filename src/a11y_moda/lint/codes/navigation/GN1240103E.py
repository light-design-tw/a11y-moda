"""GN1240103E lint — pages with many links should group them in <nav>.

HTML only. Threshold: ≥10 anchors total with no <nav> on the page → fail.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, _html_tag_name, get_html_attr


@register
class NavGroupingLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1240103E",
        guideline="2.4.1",
        level=Level.A,
        desc="頁面有多個鏈結時，應使用 <nav> 結構性分群",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        bodies = find_html_elements(parsed.tree, "body")
        if not bodies:
            return
        body = bodies[0]
        navs = self._find_descendants(body, "nav")
        if navs:
            return
        anchor_count = self._count_anchors(body)
        if anchor_count >= 10:
            yield self._issue(status="fail",
                message=f"頁面有 {anchor_count} 個鏈結但未使用 <nav> 分群",
                node=body)

    @staticmethod
    def _find_descendants(node, tag):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == tag:
                out.append(n)
            for c in n.children:
                walk(c)
        walk(node)
        return out

    @staticmethod
    def _count_anchors(body):
        n = 0
        def walk(node):
            nonlocal n
            if node.type in ("element", "self_closing_tag") and _html_tag_name(node) == "a":
                if get_html_attr(node, "href").kind in ("literal", "boolean"):
                    n += 1
            for c in node.children:
                walk(c)
        walk(body)
        return n
