"""HM3240800E lint — page should provide breadcrumb navigation (AAA).

HTML only. AAA-level. Looks for `<nav aria-label="*breadcrumb*">` or
elements with `breadcrumb` in className. Lint can't tell if a page is
the home page (URL not part of source), so we scan everything; user can
--ignore HM3240800E on landing pages.
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr, _html_tag_name


_BREADCRUMB_LABEL_RE = re.compile(r"breadcrumb|麵包屑|路徑", re.IGNORECASE)
_BREADCRUMB_CLASS_RE = re.compile(r"breadcrumb", re.IGNORECASE)


@register
class BreadcrumbLint(LintRule):
    meta = RuleMeta(
        rule_id="HM3240800E",
        guideline="2.4.8",
        level=Level.AAA,
        desc="頁面應提供麵包屑路徑導覽 (AAA)",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        bodies = find_html_elements(parsed.tree, "body")
        if not bodies:
            return
        body = bodies[0]
        if self._has_breadcrumb(body):
            return
        yield self._issue(status="info",
            message='頁面未提供麵包屑路徑導覽 (預期 nav[aria-label*=breadcrumb] 或 .breadcrumb)',
            node=body)

    def _has_breadcrumb(self, body) -> bool:
        # nav[aria-label*=breadcrumb]
        for nav in self._descendants(body, "nav"):
            label = get_html_attr(nav, "aria-label")
            if label.kind == "literal" and label.value and _BREADCRUMB_LABEL_RE.search(label.value):
                if self._has_anchor(nav):
                    return True
        # role="navigation" + aria-label*=breadcrumb
        for el in self._all_elements(body):
            role = get_html_attr(el, "role")
            if role.kind == "literal" and role.value == "navigation":
                label = get_html_attr(el, "aria-label")
                if label.kind == "literal" and label.value and _BREADCRUMB_LABEL_RE.search(label.value):
                    if self._has_anchor(el):
                        return True
        # element with class*=breadcrumb
        for el in self._all_elements(body):
            cls = get_html_attr(el, "class")
            if cls.kind == "literal" and cls.value and _BREADCRUMB_CLASS_RE.search(cls.value):
                if self._has_anchor(el):
                    return True
        return False

    @staticmethod
    def _all_elements(body):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                out.append(n)
            for c in n.children:
                walk(c)
        walk(body)
        return out

    @staticmethod
    def _descendants(node, tag):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == tag:
                out.append(n)
            for c in n.children:
                walk(c)
        walk(node)
        return out

    @staticmethod
    def _has_anchor(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == "a":
                return True
            return any(walk(c) for c in n.children)
        return walk(node)
