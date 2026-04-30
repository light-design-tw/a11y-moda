"""GN2141103E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ContrastToggleControl(Rule):
    """GN2141103E — should provide a control to switch to high-contrast presentation."""

    meta = RuleMeta(rule_id="GN2141103E", guideline="1.4.11", level=Level.AA,
        desc="提供具有足夠對比度的控制元件，以允許用戶切換到足夠對比度的呈現",
        source="extension")

    _CONTRAST_HINT = re.compile(r"(高對比|high.?contrast|dark.?mode|無障礙模式|對比切換)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if self._CONTRAST_HINT.search(soup.get_text() or ""):
            return
        report.add(self._issue(
            message="頁面未提供高對比 / 對比切換控制（可選）。",
            status="info",
        ))
