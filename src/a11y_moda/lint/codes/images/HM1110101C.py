"""HM1110101C lint — `<area>` in `<map>` needs non-empty alt.

Same status logic as HM1110100C (img alt). Imagemap usage is rare in
modern apps but still appears in legacy code; rule is cheap to run.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr, has_spread_props,
    find_html_elements, get_html_attr,
)


@register
class AreaAltLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1110101C",
        guideline="1.1.1",
        level=Level.A,
        desc="影像地圖<area>需有 alt 屬性，且其值不得為空字串",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for area in find_html_elements(parsed.tree, "area"):
                attr = get_html_attr(area, "alt")
                if attr.kind == "missing":
                    yield self._issue(status="fail",
                        message="<area> 缺 alt 屬性 — 影像地圖區域必須有替代文字",
                        node=area)
                elif attr.kind == "empty":
                    # Empty alt on <area> is unlike <img>: there's no decorative
                    # use case, so treat as fail (not info).
                    yield self._issue(status="fail",
                        message="<area> alt 為空字串 — 影像地圖區域必須有非空替代文字",
                        node=area)
            return

        for area in find_jsx_elements(parsed.tree, "area"):
            attr = get_attr(area, "alt")
            if attr.kind == "missing" and has_spread_props(area):
                yield self._issue(status="caveat",
                    message="<area> 透過 {...spread} 帶屬性 — alt 可能在 spread 內，無法靜態驗證",
                    node=area)
                continue
            if attr.kind == "missing":
                yield self._issue(status="fail",
                    message="<area> 缺 alt 屬性 — 影像地圖區域必須有替代文字",
                    node=area)
            elif attr.kind in ("empty", "boolean"):
                yield self._issue(status="fail",
                    message="<area> alt 為空 — 影像地圖區域必須有非空替代文字",
                    node=area)
            elif attr.kind == "dynamic":
                yield self._issue(status="caveat",
                    message=f"<area> alt 為動態值 ({attr.raw}) — 無法靜態驗證內容品質",
                    node=area)
