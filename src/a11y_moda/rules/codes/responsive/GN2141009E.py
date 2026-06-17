"""GN2141009E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class ReflowNoHorizontalScroll(Rule):
    """GN2141009E — content must reflow at 320px width without horizontal scroll (1.4.10)."""

    meta = RuleMeta(
        rule_id="GN2141009E",
        guideline="1.4.10",
        level=Level.AA,
        desc="頁面內容應能在 320 CSS 像素寬度下重排，不需水平捲動（可水平捲動的區域面板亦須容納其中）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        r = getattr(ctx, "reflow", None)
        if not ctx.browser_used or r is None or getattr(r, "error", ""):
            return
        if not r.has_horizontal_scroll:
            return
        report.add(self._issue(
            message=(
                f"頁面在 {r.width_tested}px 寬度下仍需水平捲動"
                f"（內容寬 {r.scroll_width}px ＞ 視區 {r.client_width}px），未符合 1.4.10 重排要求。"
                f"請改用響應式版面，避免固定寬度容器或不換行的大型元素 / 表格。"
            ),
            snippet=f"scrollWidth={r.scroll_width} clientWidth={r.client_width} @ {r.width_tested}px",
        ))
