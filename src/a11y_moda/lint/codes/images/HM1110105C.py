"""HM1110105C lint — `<applet>` / `<embed>` / `<object>` need text alternative.

These elements can carry their alternative content either via `alt`/
`title`/`aria-label` attributes, or via inner text / inner non-`<param>`
children (the rendered fallback). At lint time we can detect attribute
presence; inner content is only partially observable for `<object>`
because the inner JSX may be dynamic.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any, get_attr, has_spread_props,
    find_html_elements, get_html_attr,
)


def _has_text_alternative_jsx(elem) -> bool:
    """True if alt/title/aria-label is a literal non-empty string. Doesn't
    handle dynamic values (caller emits caveat for those)."""
    for attr_name in ("alt", "title", "aria-label", "aria-labelledby"):
        a = get_attr(elem, attr_name)
        if a.kind == "literal" and a.value:
            return True
    return False


def _has_dynamic_attrs_jsx(elem) -> bool:
    for attr_name in ("alt", "title", "aria-label", "aria-labelledby"):
        a = get_attr(elem, attr_name)
        if a.kind == "dynamic":
            return True
    return False


@register
class ObjectAltLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1110105C",
        guideline="1.1.1",
        level=Level.A,
        desc="<applet>/<embed>/<object> 需有替代文字內容 (alt/title/aria-label 或內文)",
        source="freego",
    )

    _TARGETS = ("applet", "embed", "object")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in self._TARGETS:
                for el in find_html_elements(parsed.tree, tag):
                    if any((get_html_attr(el, a).kind == "literal" and
                            get_html_attr(el, a).value)
                           for a in ("alt", "title", "aria-label", "aria-labelledby")):
                        continue
                    yield self._issue(
                        status="info",
                        message=f"<{tag}> 無 alt/title/aria-label — 請確認元素內有替代文字內容 (lint 看不見渲染後 fallback)",
                        node=el)
            return

        for el in find_jsx_elements_any(parsed.tree, self._TARGETS):
            name = next((c.text.decode("utf-8", errors="replace")
                         for c in el.children if c.type == "identifier"), "?")
            if has_spread_props(el):
                yield self._issue(
                    status="caveat",
                    message=f"<{name}> 透過 {{...spread}} 帶屬性 — 替代文字可能在 spread 內",
                    node=el)
                continue
            if _has_text_alternative_jsx(el):
                continue
            if _has_dynamic_attrs_jsx(el):
                yield self._issue(
                    status="caveat",
                    message=f"<{name}> 替代文字屬性為動態值 — 無法靜態驗證",
                    node=el)
                continue
            # No literal alt/title/aria-* found. Inner content might still
            # provide a fallback, but we can't easily verify (children may be
            # dynamic JSX). Surface as info, not fail.
            yield self._issue(
                status="info",
                message=f"<{name}> 無 alt/title/aria-label 屬性 — 請確認元素內有替代文字內容",
                node=el)
