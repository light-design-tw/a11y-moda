"""HM1240102C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NavGroupsLinks(Rule):
    """HM1240102C — <nav> must not be empty."""

    meta = RuleMeta(
        rule_id="HM1240102C",
        guideline="2.4.1",
        level=Level.A,
        desc="以導覽<nav>標籤將相關鏈結組件做分群",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for nav in soup.find_all("nav"):
            if not isinstance(nav, Tag) or should_skip(nav):
                continue
            if not [c for c in nav.find_all(recursive=False) if isinstance(c, Tag)]:
                report.add(self._issue(
                    message="使用nav元素群組鏈結組件，其內容不可為空值。",
                    snippet=truncate(str(nav), 100),
                ))
                return
