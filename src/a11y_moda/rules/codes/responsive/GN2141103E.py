"""GN2141103E rule."""
from __future__ import annotations
import re
from ....models import Level
from ...base import Rule, RuleMeta, register


@register
class ContrastToggleControl(Rule):
    """GN2141103E — should provide a control to switch to high-contrast presentation."""

    meta = RuleMeta(rule_id="GN2141103E", guideline="1.4.11", level=Level.AA,
        desc="提供具有足夠對比度的控制元件，以允許用戶切換到足夠對比度的呈現",
        source="extension")

    _CONTRAST_HINT = re.compile(
        r"(高對比|high.?contrast|dark.?mode|light.?mode|無障礙模式"
        r"|對比切換|深色模式|淺色模式|主題切換|切換主題|theme.?toggle)",
        re.IGNORECASE,
    )

    def _check(self, soup, report, *, html, url, ctx) -> None:
        # Many sites label the toggle via aria-label/title/alt on an
        # icon-only button — visible text alone misses those.
        text_pool = soup.get_text() or ""
        for el in soup.find_all(["button", "a", "input"]):
            for attr in ("aria-label", "title", "alt"):
                v = el.get(attr)
                if v:
                    text_pool += " " + v
        if self._CONTRAST_HINT.search(text_pool):
            return
        report.add(self._issue(
            message="頁面未提供高對比 / 對比切換控制（可選）。",
            status="info",
        ))
