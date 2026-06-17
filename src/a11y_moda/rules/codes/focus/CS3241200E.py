"""CS3241200E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class FocusNotObscuredEnhanced(Rule):
    """CS3241200E — no part of a focused element may be hidden by sticky/fixed content (2.4.12)."""

    meta = RuleMeta(
        rule_id="CS3241200E",
        guideline="2.4.12",
        level=Level.AAA,
        desc="鍵盤焦點落在元件上時，該元件不應有任何部分被作者建立的內容（如黏性頁首/頁尾）遮蔽",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used or not ctx.tab_stops:
            return
        # 2.4.12 Enhanced: ANY part covered fails (cf. FA2241100E / 2.4.11 which
        # only fails on entirely hidden). The probe's `obscured` flag is set
        # when any sample point of the focused element sits under a
        # position:sticky/fixed ancestor.
        covered = [s for s in ctx.tab_stops if getattr(s, "obscured", False)]
        if not covered:
            return
        sample = covered[0]
        report.add(self._issue(
            message=(
                f"鍵盤焦點被黏性(sticky/fixed)內容部分或完全遮蔽 — {len(covered)}/{len(ctx.tab_stops)} "
                f"個 focusable 元素聚焦時有部分被固定元件覆蓋，未達焦點不被遮(增強，2.4.12)。"
                f"請以 scroll-padding 預留固定元件高度，或調整其版面。"
            ),
            snippet=f"{sample.tag} {sample.selector} @ y={sample.bbox[1]:.0f}",
        ))
