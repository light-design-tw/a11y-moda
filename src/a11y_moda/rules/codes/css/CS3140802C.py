"""CS3140802C rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from ....css_utils import collect_declarations
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class LineHeightDeclared(Rule):
    """CS3140802C — at least one CSS rule must declare line-height."""

    meta = RuleMeta(
        rule_id="CS3140802C",
        guideline="1.4.8",
        level=Level.AAA,
        desc="需有CSS樣式規則指定行距(line-height)",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        decls = collect_declarations(soup, url)
        if any(d.prop == "line-height" for d in decls):
            return
        status = "info" if ctx.freego_compat else "fail"
        report.add(self._issue(message="未發現任何指定 line-height 的 CSS 規則。", status=status))
