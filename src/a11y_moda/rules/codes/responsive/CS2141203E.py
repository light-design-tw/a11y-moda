"""CS2141203E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class LineHeightInCss(Rule):
    """CS2141203E — line-height should be set in CSS."""

    meta = RuleMeta(rule_id="CS2141203E", guideline="1.4.12", level=Level.AA,
        desc="以CSS設定行間距",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        if any(d.prop == "line-height" for d in decls):
            return
        report.add(self._issue(
            message="未發現任何 CSS line-height 設定。",
            status="info",
        ))
