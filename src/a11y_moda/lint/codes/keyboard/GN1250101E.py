"""GN1250101E lint — custom slider should use <input type=range> or role=slider."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr, _html_tag_name


_SLIDER_HINT = re.compile(r"slider|range", re.IGNORECASE)


@register
class SliderUsesRangeLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1250101E",
        guideline="2.5.1",
        level=Level.A,
        desc="自訂滑塊應使用 <input type=range> 或 role=slider + aria-valuenow",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                cls = get_html_attr(el, "class")
                if cls.kind != "literal" or not cls.value or not _SLIDER_HINT.search(cls.value):
                    continue
                # Has input[type=range] inside?
                if self._html_has_range_input(el):
                    continue
                role = get_html_attr(el, "role")
                if role.kind == "literal" and role.value == "slider":
                    if get_html_attr(el, "aria-valuenow").kind != "missing":
                        continue
                yield self._issue(status="info",
                    message="疑似自訂滑塊未用 <input type=range> 也未提供 role=slider + aria-valuenow",
                    node=el)
                return
            return

        for el in find_jsx_elements(parsed.tree):
            cls = get_attr(el, "className")
            if cls.kind == "missing":
                cls = get_attr(el, "class")
            if cls.kind != "literal" or not cls.value or not _SLIDER_HINT.search(cls.value):
                continue
            parent = el.parent if el.type == "jsx_opening_element" else el
            if self._jsx_has_range_input(parent):
                continue
            role = get_attr(el, "role")
            if role.kind == "literal" and role.value == "slider":
                if get_attr(el, "aria-valuenow").kind != "missing":
                    continue
            yield self._issue(status="info",
                message="疑似自訂滑塊未用 <input type=range> 也未提供 role=slider + aria-valuenow",
                node=el)
            return

    @staticmethod
    def _html_has_range_input(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == "input":
                t = get_html_attr(n, "type")
                if t.kind == "literal" and t.value == "range":
                    return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _jsx_has_range_input(jsx_element) -> bool:
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in n.children if c.type == "identifier"), "")
                if tag == "input":
                    t = get_attr(n, "type")
                    if t.kind == "literal" and t.value == "range":
                        return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
