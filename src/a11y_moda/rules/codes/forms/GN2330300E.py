"""GN2330300E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class ErrorFocusJump(Rule):
    """GN2330300E — empty submit must move focus to the first invalid required field."""

    meta = RuleMeta(
        rule_id="GN2330300E",
        guideline="3.3.3",
        level=Level.AA,
        desc="表單必填欄位驗證失敗時，焦點應跳至第一個錯誤欄位",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.form_sims:
            return
        offenders = [s for s in ctx.form_sims
                     if s.has_required and s.submit_clicked and not s.error_focus_jumped]
        if not offenders:
            return
        s = offenders[0]
        target = s.focus_after_submit_selector or s.focus_after_submit_tag or "(無焦點)"
        report.add(self._issue(
            message=f"表單 {s.selector} 留空送出後焦點未跳至錯誤欄（停留在 {target}），鍵盤使用者難以定位錯誤。",
        ))
