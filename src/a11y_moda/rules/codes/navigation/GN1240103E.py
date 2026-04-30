"""GN1240103E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NavGroupsAnchors(Rule):
    """GN1240103E — repeated link blocks should be wrapped in <nav>."""

    meta = RuleMeta(
        rule_id="GN1240103E",
        guideline="2.4.1",
        level=Level.A,
        desc="使用結構性組件來將鏈結分群",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        navs = [n for n in soup.find_all("nav") if isinstance(n, Tag) and not should_skip(n)]
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        link_count = len([a for a in body.find_all("a", href=True) if isinstance(a, Tag) and not should_skip(a)])
        if link_count >= 10 and not navs:
            report.add(self._issue(
                message=f"頁面有 {link_count} 個鏈結但未使用 <nav> 分群。",
            ))
