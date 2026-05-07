"""HM1310100C lint — `<html>` must have a `lang` attribute.

HTML only. JSX root pages typically don't render `<html>` from source —
the root tag is provided by the framework's document layout. Defer JSX
detection to scan stage.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


@register
class HtmlLangLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1310100C",
        guideline="3.1.1",
        level=Level.A,
        desc="<html> 需有 lang 屬性，且其值不得為空",
        source="freego",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        # Find <html> root. Some HTML fragments don't have <html> at all
        # (partial templates) — don't fire there.
        roots = find_html_elements(parsed.tree, "html")
        if not roots:
            return
        for root in roots:
            attr = get_html_attr(root, "lang")
            if attr.kind == "missing":
                yield self._issue(
                    status="fail",
                    message="<html> 缺 lang 屬性 — 必須宣告網頁語系 (例: <html lang=\"zh-TW\">)",
                    node=root,
                )
            elif attr.kind == "empty":
                yield self._issue(
                    status="fail",
                    message="<html lang> 為空字串 — 必須提供有效語系標記",
                    node=root,
                )
            return  # only check the first <html>
