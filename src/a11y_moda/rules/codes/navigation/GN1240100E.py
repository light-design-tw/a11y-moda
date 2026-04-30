"""GN1240100E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class SkipLinkPresent(Rule):
    """GN1240100E — page should expose a skip-to-main-content link near the top."""

    meta = RuleMeta(
        rule_id="GN1240100E",
        guideline="2.4.1",
        level=Level.A,
        desc="在每一個頁面頂端加入一個鏈結，直接連往主要的內容區域",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        anchors = [a for a in body.find_all("a", href=True) if isinstance(a, Tag)][:8]
        for a in anchors:
            href = (a.get("href") or "").strip()
            if href.startswith("#") and len(href) > 1:
                target = soup.find(id=href[1:])
                if target is not None:
                    return
        report.add(self._issue(
            message="未發現指向主要內容的 skip link（通常為頁首第一個 <a href=\"#main\">）。",
        ))
