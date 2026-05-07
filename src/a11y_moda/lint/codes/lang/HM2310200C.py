"""HM2310200C lint — inline `lang` attributes must be non-empty and differ
from the page-level `<html lang>`.

HTML only. JSX root rarely renders <html>; defer to scan.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


@register
class LangSwitchLint(LintRule):
    meta = RuleMeta(
        rule_id="HM2310200C",
        guideline="3.1.2",
        level=Level.AA,
        desc="內文 lang 屬性需非空且與 <html lang> 不同",
        source="freego",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        roots = find_html_elements(parsed.tree, "html")
        if not roots:
            return
        page_lang_attr = get_html_attr(roots[0], "lang")
        if page_lang_attr.kind != "literal" or not page_lang_attr.value:
            return
        page_lang = page_lang_attr.value.strip()

        bodies = find_html_elements(parsed.tree, "body")
        if not bodies:
            return
        body = bodies[0]
        for el in self._descendants_with_lang(body):
            lang = get_html_attr(el, "lang")
            if lang.kind == "empty":
                yield self._issue(status="fail",
                    message="內文 lang 屬性為空字串",
                    node=el)
                return
            if lang.kind == "literal" and lang.value and lang.value.strip() == page_lang:
                yield self._issue(status="fail",
                    message=f'內文 lang="{lang.value}" 與 <html lang="{page_lang}"> 重複，無切換意義',
                    node=el)
                return

    @staticmethod
    def _descendants_with_lang(node):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                attr = get_html_attr(n, "lang")
                if attr.kind != "missing":
                    out.append(n)
            for c in n.children:
                walk(c)
        walk(node)
        return out
