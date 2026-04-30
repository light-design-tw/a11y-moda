"""HM3241000C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class HeadingsOrganizePage(Rule):
    """HM3241000C — pages should use heading components (no-op if HTML5 + headings present)."""

    meta = RuleMeta(
        rule_id="HM3241000C",
        guideline="2.4.10",
        level=Level.AAA,
        desc="使用標題(headings)組件來組織網頁內容",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        is_html5 = (html or "").lstrip().lower().startswith("<!doctype html>")
        if is_html5:
            return
        if not ctx.state.get("HM1130100C_ok", True):
            report.add(self._issue(
                message="非HTML5且未提供標題組件，無法協助組織網頁。",
            ))
