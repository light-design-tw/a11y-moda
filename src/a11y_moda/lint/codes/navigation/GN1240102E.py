"""GN1240102E lint — page should have <main> landmark or id="main"/"content".

HTML only — same reason as other page-level rules.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr, _html_tag_name


_MAIN_IDS = {"main", "content", "maincontent"}


@register
class MainContentAnchorLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1240102E",
        guideline="2.4.1",
        level=Level.A,
        desc="頁面應有 <main> landmark 或 id=\"main\"/\"content\" 內容錨點",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        bodies = find_html_elements(parsed.tree, "body")
        if not bodies:
            return
        body = bodies[0]
        if self._has_main(body):
            return
        yield self._issue(status="fail",
            message='頁面缺 <main> landmark 或 id="main"/"content" 錨點',
            node=body)

    def _has_main(self, body) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                if _html_tag_name(n) == "main":
                    return True
                role = get_html_attr(n, "role")
                if role.kind == "literal" and role.value and role.value.lower() == "main":
                    return True
                el_id = get_html_attr(n, "id")
                if el_id.kind == "literal" and el_id.value and el_id.value.lower() in _MAIN_IDS:
                    return True
            return any(walk(c) for c in n.children)
        return walk(body)
