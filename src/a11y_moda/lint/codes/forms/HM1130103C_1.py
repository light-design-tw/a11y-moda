"""HM1130103C_1 lint — `<optgroup>` inside `<select>` needs unique non-empty label.

Walk every `<select>`. For each `<optgroup>` child, check the `label`
attribute: missing/empty/dynamic gets a status; duplicates within the
same `<select>` are a fail.
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
class OptgroupLabelLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130103C_1",
        guideline="1.3.1",
        level=Level.A,
        desc="<optgroup> 需有 label 屬性，非空且不重複",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for sel in find_html_elements(parsed.tree, "select"):
                seen: set[str] = set()
                for og in self._html_descendants(sel, "optgroup"):
                    a = get_html_attr(og, "label")
                    if a.kind == "missing":
                        yield self._issue(status="fail",
                            message="<optgroup> 缺 label 屬性",
                            node=og)
                        continue
                    if a.kind == "empty":
                        yield self._issue(status="fail",
                            message="<optgroup> label 為空字串",
                            node=og)
                        continue
                    if a.kind == "literal" and a.value in seen:
                        yield self._issue(status="fail",
                            message=f'<optgroup> label="{a.value}" 重複，必須唯一',
                            node=og)
                        continue
                    if a.kind == "literal" and a.value:
                        seen.add(a.value)
            return

        for sel in find_jsx_elements(parsed.tree, "select"):
            parent = sel.parent if sel.type == "jsx_opening_element" else sel
            seen: set[str] = set()
            for og in self._jsx_descendants(parent, "optgroup"):
                a = get_attr(og, "label")
                if a.kind == "missing":
                    yield self._issue(status="fail",
                        message="<optgroup> 缺 label 屬性",
                        node=og)
                    continue
                if a.kind in ("empty", "boolean"):
                    yield self._issue(status="fail",
                        message="<optgroup> label 為空",
                        node=og)
                    continue
                if a.kind == "dynamic":
                    yield self._issue(status="caveat",
                        message=f"<optgroup> label 為動態值 ({a.raw}) — 無法靜態驗證唯一性",
                        node=og)
                    continue
                if a.kind == "literal" and a.value in seen:
                    yield self._issue(status="fail",
                        message=f'<optgroup> label="{a.value}" 重複',
                        node=og)
                    continue
                if a.kind == "literal" and a.value:
                    seen.add(a.value)

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
