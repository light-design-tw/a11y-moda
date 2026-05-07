"""HM1130200C lint — `dir="rtl"` element should expose `lang` attribute too.

When mixing right-to-left content (Arabic, Hebrew), the dir attribute
alone doesn't tell screen readers what language the text is in. Pair
with lang.
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
class BidiTextLangLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130200C",
        guideline="1.3.2",
        level=Level.A,
        desc='dir="rtl" 元素應有 lang 屬性標示語系',
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                d = get_html_attr(el, "dir")
                if d.kind != "literal" or not d.value or d.value.lower() != "rtl":
                    continue
                if get_html_attr(el, "lang").kind != "missing":
                    continue
                yield self._issue(status="fail",
                    message='dir="rtl" 元素缺 lang 屬性 — 應標示文字語系',
                    node=el)
                return
            return

        for el in find_jsx_elements(parsed.tree):
            d = get_attr(el, "dir")
            if d.kind != "literal" or not d.value or d.value.lower() != "rtl":
                continue
            if get_attr(el, "lang").kind != "missing":
                continue
            yield self._issue(status="fail",
                message='dir="rtl" 元素缺 lang 屬性 — 應標示文字語系',
                node=el)
            return
