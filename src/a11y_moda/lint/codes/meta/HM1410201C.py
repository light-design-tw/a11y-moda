"""HM1410201C lint — `<frame>` / `<iframe>` need non-empty title.

`<frame>` is HTML 4 frameset (legacy); `<iframe>` is the common modern
case. Both lint identically.
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


@register
class FrameTitleLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1410201C",
        guideline="4.1.2",
        level=Level.A,
        desc="<iframe> / <frame> 需有 title 屬性，且其值不得為空",
        source="freego",
    )

    _TARGETS = ("iframe", "frame")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in self._TARGETS:
                for el in find_html_elements(parsed.tree, tag):
                    attr = get_html_attr(el, "title")
                    if attr.kind == "missing":
                        yield self._issue(status="fail",
                            message=f"<{tag}> 缺 title 屬性 — 必須提供頁框名稱協助辨識",
                            node=el)
                    elif attr.kind == "empty":
                        yield self._issue(status="fail",
                            message=f"<{tag}> title 為空字串 — 必須提供非空頁框名稱",
                            node=el)
            return

        for el in find_jsx_elements_any(parsed.tree, self._TARGETS):
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in el.children if c.type == "identifier"), "?")
            if has_spread_props(el):
                yield self._issue(status="caveat",
                    message=f"<{tag}> 透過 {{...spread}} 帶屬性 — title 可能在 spread 內",
                    node=el)
                continue
            attr = get_attr(el, "title")
            if attr.kind == "missing":
                yield self._issue(status="fail",
                    message=f"<{tag}> 缺 title 屬性 — 必須提供頁框名稱",
                    node=el)
            elif attr.kind in ("empty", "boolean"):
                yield self._issue(status="fail",
                    message=f"<{tag}> title 為空 — 必須提供非空頁框名稱",
                    node=el)
            elif attr.kind == "dynamic":
                yield self._issue(status="caveat",
                    message=f"<{tag}> title 為動態值 ({attr.raw}) — 無法靜態驗證",
                    node=el)
