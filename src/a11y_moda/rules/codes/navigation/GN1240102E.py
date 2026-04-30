"""GN1240102E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TopOfPageJumpToContent(Rule):
    """GN1240102E — top-of-page link to content area (often same as skip link)."""

    meta = RuleMeta(rule_id="GN1240102E", guideline="2.4.1", level=Level.A,
        desc="在頁面頂端加入鏈結，連到該頁面的內容區域的開頭位置",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        if body.find("main"):
            return
        if body.find(attrs={"role": "main"}):
            return
        if body.find(id="main") or body.find(id="content") or body.find(id="maincontent"):
            return
        report.add(self._issue(
            message="頁面缺少 <main> landmark 或 id=\"main\"/\"content\" 內容錨點。",
        ))
