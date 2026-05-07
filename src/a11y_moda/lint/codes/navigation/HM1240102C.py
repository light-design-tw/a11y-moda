"""HM1240102C lint — `<nav>` must not be empty (must contain links/content)."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, find_html_elements, has_spread_props


@register
class NavNotEmptyLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1240102C",
        guideline="2.4.1",
        level=Level.A,
        desc="<nav> 元素內容不可為空",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for nav in find_html_elements(parsed.tree, "nav"):
                if not self._html_has_element_child(nav):
                    yield self._issue(status="fail",
                        message="<nav> 為空 — 必須包含鏈結組件",
                        node=nav)
            return

        for nav in find_jsx_elements(parsed.tree, "nav"):
            if nav.type == "jsx_self_closing_element":
                if has_spread_props(nav):
                    continue  # wrapper component
                yield self._issue(status="fail",
                    message="<nav /> 為空 — 必須包含鏈結組件",
                    node=nav)
                continue
            parent = nav.parent
            has_static, has_dynamic = self._jsx_body_signals(parent)
            if has_static:
                continue
            if has_dynamic:
                continue  # wrapper / dynamic content; defer to scan
            yield self._issue(status="fail",
                message="<nav> 為空 — 必須包含鏈結組件",
                node=nav)

    @staticmethod
    def _html_has_element_child(node) -> bool:
        for child in node.children:
            if child.type in ("element", "self_closing_tag"):
                return True
        return False

    @staticmethod
    def _jsx_body_signals(jsx_element):
        """Returns (has_static_element_child, has_dynamic_expression)."""
        has_static = False
        has_dynamic = False
        for child in jsx_element.children:
            if child.type in ("jsx_opening_element", "jsx_closing_element",
                              "jsx_self_closing_element", "jsx_text"):
                continue
            if child.type == "jsx_expression":
                has_dynamic = True
                continue
            if child.type in ("jsx_element", "jsx_self_closing_element"):
                has_static = True
        return has_static, has_dynamic
