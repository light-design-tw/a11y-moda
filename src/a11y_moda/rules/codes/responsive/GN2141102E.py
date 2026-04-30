"""GN2141102E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class AdjacentColorBoundary(Rule):
    """GN2141102E — adjacent color boundaries should be perceivable."""

    meta = RuleMeta(rule_id="GN2141102E", guideline="1.4.11", level=Level.AA,
        desc="在相鄰顏色之間的邊界處提供足夠的對比度",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        suspect = 0
        for d in decls:
            if "border" not in d.prop:
                continue
            v = d.value.lower()
            if re.search(r"#([def])\1\1", v) or re.search(r"#[def]{2}[def]{2}[def]{2}", v):
                suspect += 1
            if "rgba" in v and re.search(r"rgba\([^)]*,\s*0\.\d", v):
                suspect += 1
        if suspect >= 5:
            report.add(self._issue(
                message=f"頁面有 {suspect} 處邊框使用淺色 / 半透明，相鄰區域對比可能不足。",
                status="info",
            ))
