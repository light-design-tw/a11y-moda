"""CS2141001E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class HasFlexOrGrid(Rule):
    """CS2141001E — pages should use flex/grid for layout reflow."""

    meta = RuleMeta(rule_id="CS2141001E", guideline="1.4.10", level=Level.AA,
        desc="使用CSS彈性容器重排內容",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        for d in decls:
            if d.prop == "display" and any(v in d.value.lower() for v in ("flex", "grid", "inline-flex", "inline-grid")):
                return
        report.add(self._issue(
            message="未發現 display:flex / grid，現代響應式佈局可能不足。",
            status="info",
        ))
