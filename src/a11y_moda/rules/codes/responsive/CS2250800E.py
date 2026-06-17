"""CS2250800E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register

# 2.5.8 Target Size (Minimum): pointer targets should be ≥ 24×24 CSS px.
_MIN_TARGET_PX = 24.0


@register
class TargetSizeMinimum(Rule):
    """CS2250800E — pointer targets must be at least 24×24px (2.5.8)."""

    meta = RuleMeta(
        rule_id="CS2250800E",
        guideline="2.5.8",
        level=Level.AA,
        desc="指標目標的尺寸應至少為 24×24 CSS 像素，以確保可被準確點選或觸控",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # Reuses the focus-walk bbox (focusable ≈ pointer target). No new probe.
        if not ctx.browser_used or not ctx.tab_stops:
            return
        # Conservative: only flag when BOTH dimensions are under 24px — a genuine
        # icon-sized target. A short-but-wide element (e.g. an inline text link
        # ~20px tall but 100px wide) is left alone; 2.5.8's inline / spacing
        # exceptions usually cover those and flagging them is FP-prone.
        tiny = [
            s for s in ctx.tab_stops
            if 0 < s.bbox[2] < _MIN_TARGET_PX and 0 < s.bbox[3] < _MIN_TARGET_PX
        ]
        if not tiny:
            return
        sample = tiny[0]
        report.add(self._issue(
            message=(
                f"指標目標過小 — {len(tiny)}/{len(ctx.tab_stops)} 個可操作元素的尺寸小於 "
                f"{_MIN_TARGET_PX:.0f}×{_MIN_TARGET_PX:.0f}px（例：{sample.bbox[2]:g}×{sample.bbox[3]:g}px），"
                f"觸控/點選不易。請放大目標或加足夠間距（行內文字連結等例外不在此限）。"
            ),
            snippet=f"{sample.tag} {sample.selector} {sample.bbox[2]:g}×{sample.bbox[3]:g}px",
        ))
