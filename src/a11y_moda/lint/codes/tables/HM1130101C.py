"""HM1130101C lint — data table <th> needs scope or id when spanning cells.

Walks each <table>. For each <th> inside, if it has colspan/rowspan but
no scope or id, emit fail.
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
class TableScopeLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130101C",
        guideline="1.3.1",
        level=Level.A,
        desc="表格 <th> 跨欄/列 (colspan/rowspan) 時需 scope 或 id 屬性",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tbl in find_html_elements(parsed.tree, "table"):
                for th in self._html_descendants(tbl, "th"):
                    has_span = (get_html_attr(th, "colspan").kind != "missing"
                                or get_html_attr(th, "rowspan").kind != "missing")
                    if not has_span:
                        continue
                    if (get_html_attr(th, "scope").kind != "missing"
                            or get_html_attr(th, "id").kind != "missing"):
                        continue
                    yield self._issue(status="fail",
                        message="跨欄/列 <th> 需 scope 或 id 屬性建立關聯",
                        node=th)
                    break
            return

        for tbl in find_jsx_elements(parsed.tree, "table"):
            parent = tbl.parent if tbl.type == "jsx_opening_element" else tbl
            for th in self._jsx_descendants(parent, "th"):
                has_span = (get_attr(th, "colspan").kind != "missing"
                            or get_attr(th, "rowspan").kind != "missing")
                if not has_span:
                    continue
                if (get_attr(th, "scope").kind != "missing"
                        or get_attr(th, "id").kind != "missing"):
                    continue
                yield self._issue(status="fail",
                    message="跨欄/列 <th> 需 scope 或 id 屬性建立關聯",
                    node=th)
                break

    @staticmethod
    def _html_descendants(node, tag):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == tag:
                out.append(n)
            for c in n.children:
                walk(c)
        walk(node)
        return out

    @staticmethod
    def _jsx_descendants(node, tag):
        out = []
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for c in n.children:
                    if c.type == "identifier" and c.text.decode("utf-8", errors="replace") == tag:
                        out.append(n)
                        break
            for c in n.children:
                walk(c)
        walk(node)
        return out
