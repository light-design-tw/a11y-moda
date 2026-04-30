"""CS2240700E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class FocusVisible(Rule):
    """CS2240700E — focused element must show a visible focus indicator."""

    meta = RuleMeta(
        rule_id="CS2240700E",
        guideline="2.4.7",
        level=Level.AA,
        desc="使用者介面取得焦點時，使其鍵盤焦點指示具高可見度",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used or not ctx.tab_stops:
            return
        invisible = [s for s in ctx.tab_stops if not s.has_visible_outline]
        if not invisible:
            return
        sample = invisible[0]
        report.add(self._issue(
            message=f"鍵盤焦點不可見 — {len(invisible)}/{len(ctx.tab_stops)} 個 focusable 元素缺 :focus-visible 樣式。",
            snippet=f"{sample.selector} text={sample.text!r}",
        ))
