"""CS2141201E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TextSpacingNoNowrap(Rule):
    """CS2141201E — adjusting spacing should not break content with white-space:nowrap everywhere."""

    meta = RuleMeta(rule_id="CS2141201E", guideline="1.4.12", level=Level.AA,
        desc="允許調整文字間距而不換行(wrapping)",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        nowrap = sum(1 for d in decls if d.prop == "white-space" and "nowrap" in d.value.lower())
        if nowrap >= 3:
            report.add(self._issue(
                message=f"頁面有 {nowrap} 處 white-space:nowrap，使用者放寬字距時容易溢出。",
                status="info",
            ))
