"""FA2241100E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class FocusNotObscuredMinimum(Rule):
    """FA2241100E — focused element must not be entirely hidden by sticky/fixed content (2.4.11)."""

    meta = RuleMeta(
        rule_id="FA2241100E",
        guideline="2.4.11",
        level=Level.AA,
        desc="鍵盤焦點落在元件上時，該元件不應因作者建立的內容（如黏性頁首/頁尾）而完全被遮蔽",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # Needs the rendered Tab walk — `obscured_fully` is computed live by the
        # probe (browsers scroll focus into view but ignore sticky overlays).
        if not ctx.browser_used or not ctx.tab_stops:
            return
        # 2.4.11 Minimum: a failure is the focused element being *entirely*
        # hidden. The probe flags obscured_fully when every in-viewport sample
        # point of the element's box is covered by a position:sticky/fixed
        # ancestor — partial cover (allowed at AA) is not flagged here.
        hidden = [s for s in ctx.tab_stops if getattr(s, "obscured_fully", False)]
        if not hidden:
            return
        sample = hidden[0]
        report.add(self._issue(
            message=(
                f"鍵盤焦點被黏性(sticky/fixed)內容完全遮蔽 — {len(hidden)}/{len(ctx.tab_stops)} "
                f"個 focusable 元素聚焦時整個被頁首/頁尾類固定元素覆蓋，使用者看不到焦點落點。"
                f"請在目標元素加 scroll-margin，或縮減固定元件高度。"
            ),
            snippet=f"{sample.tag} {sample.selector} @ y={sample.bbox[1]:.0f}",
        ))
