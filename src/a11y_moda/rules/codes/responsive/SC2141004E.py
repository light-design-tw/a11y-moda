"""SC2141004E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ProportionalSize(Rule):
    """SC2141004E — sizes should scale proportionally with text size."""

    meta = RuleMeta(rule_id="SC2141004E", guideline="1.4.10", level=Level.AA,
        desc="使用與文字大小成比例的方式計算大小和位置",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        rel_count = 0
        abs_count = 0
        for d in decls:
            if d.prop in ("width", "height", "padding", "margin"):
                v = d.value.lower()
                if v.endswith(("em", "rem", "%", "ch")):
                    rel_count += 1
                elif re.search(r"\d(px|pt|pc|in|cm|mm)", v):
                    abs_count += 1
        if abs_count > rel_count * 3 and abs_count > 20:
            report.add(self._issue(
                message=f"頁面 padding/margin/width/height 大量使用絕對單位（{abs_count} 處 vs {rel_count} 相對），不利字級放大。",
                status="info",
            ))
