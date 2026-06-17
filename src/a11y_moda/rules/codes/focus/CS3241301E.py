"""CS3241301E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register

# 2.4.13 Focus Appearance expects an indicator at least as large as a 2px-thick
# perimeter of the component. We approximate "strong" by outline thickness.
_MIN_FOCUS_OUTLINE_PX = 2.0


@register
class FocusBorderStrong(Rule):
    """CS3241301E — focus indicator must be a strong border (≥2px), not merely present (2.4.13)."""

    meta = RuleMeta(
        rule_id="CS3241301E",
        guideline="2.4.13",
        level=Level.AAA,
        desc="在組件內建立強而明顯的焦點指示框線（焦點外觀，AAA）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used or not ctx.tab_stops:
            return
        # Presence of *any* focus indicator is CS2240700E's job (2.4.7). 2.4.13
        # raises the bar to a substantial border. Only judge elements that
        # already show an indicator; a box-shadow-only indicator can't be
        # measured by outline width here → caveat for manual review.
        thin = [s for s in ctx.tab_stops
                if s.has_visible_outline and 0 < s.outline_width < _MIN_FOCUS_OUTLINE_PX]
        shadow_only = [s for s in ctx.tab_stops
                       if s.has_visible_outline and s.outline_width == 0]
        if thin:
            sample = thin[0]
            report.add(self._issue(
                message=(
                    f"焦點框線過細 — {len(thin)}/{len(ctx.tab_stops)} 個元素聚焦時 outline 寬度 "
                    f"< {_MIN_FOCUS_OUTLINE_PX:.0f}px，未達焦點外觀(2.4.13)「強而明顯」要求。"
                    f"建議 outline 至少 2px，並與相鄰色彩具足夠對比。"
                ),
                snippet=f"{sample.tag} {sample.selector} outline={sample.outline_width:g}px",
            ))
            return
        if shadow_only:
            sample = shadow_only[0]
            report.add(self._issue(
                message=(
                    f"焦點指示僅以 box-shadow 呈現（{len(shadow_only)} 個元素），"
                    f"無法量測框線厚度是否達 2.4.13 焦點外觀要求，請人工確認其面積與對比。"
                ),
                snippet=f"{sample.tag} {sample.selector}",
                status="caveat",
            ))
