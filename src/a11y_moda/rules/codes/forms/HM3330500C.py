"""HM3330500C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TitleHintForContext(Rule):
    """HM3330500C — derived: passes if HM3240900C and HM1130104C both pass."""

    meta = RuleMeta(
        rule_id="HM3330500C",
        guideline="3.3.5",
        level=Level.AAA,
        desc="使用標題(title)屬性來提供針對脈絡而作的協助說明",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.state.get("HM3240900C_ok", True):
            report.add(self._issue(message=ctx.state.get("HM3240900C_error", "鏈結title屬性使用不當")))
            return
        if not ctx.state.get("HM1130104C_ok", True):
            report.add(self._issue(message=ctx.state.get("HM1130104C_error", "表單控制元件未提供協助說明")))
