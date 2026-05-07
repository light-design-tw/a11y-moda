"""HM1110106C lint — `<img alt="">` (decorative) must not carry title/aria-*.

A decorative image (alt="") signals to screen readers "skip me". Adding
title or aria-label/aria-labelledby contradicts that signal — the reader
will still announce the title/label. This rule fires when both signals
disagree.

Static fail when both are literal. Caveat when either signal is dynamic.
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
class ImgEmptyAltNoTitleLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1110106C",
        guideline="1.1.1",
        level=Level.A,
        desc='alt="" 的 <img> 不得同時帶 title 或 aria-label/aria-labelledby',
        source="freego",
    )

    _CONFLICTING_ATTRS = ("title", "aria-label", "aria-labelledby")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for img in find_html_elements(parsed.tree, "img"):
                alt = get_html_attr(img, "alt")
                if alt.kind != "empty":
                    continue
                conflicts = [a for a in self._CONFLICTING_ATTRS
                             if get_html_attr(img, a).kind in ("literal", "boolean")]
                if conflicts:
                    yield self._issue(
                        status="fail",
                        message=f'<img alt=""> 同時帶 {",".join(conflicts)} — 裝飾圖不應提供其他文字提示',
                        node=img)
            return

        for img in find_jsx_elements(parsed.tree, "img"):
            alt = get_attr(img, "alt")
            if alt.kind != "empty":
                continue
            literal_conflicts: list[str] = []
            dynamic_conflicts: list[str] = []
            for a in self._CONFLICTING_ATTRS:
                attr = get_attr(img, a)
                if attr.kind in ("literal", "empty", "boolean"):
                    # presence regardless of value still announces something
                    literal_conflicts.append(a)
                elif attr.kind == "dynamic":
                    dynamic_conflicts.append(a)
            if literal_conflicts:
                yield self._issue(
                    status="fail",
                    message=f'<img alt=""> 同時帶 {",".join(literal_conflicts)} — 裝飾圖不應提供其他文字提示',
                    node=img)
            elif dynamic_conflicts:
                yield self._issue(
                    status="caveat",
                    message=f'<img alt=""> 帶動態 {",".join(dynamic_conflicts)} — 若 runtime 有值，與 alt="" 衝突',
                    node=img)
